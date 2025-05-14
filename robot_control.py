import YanAPI
import time
import json
import requests
from pathlib import Path
from other_functions import OtherFunctions
import nest_asyncio
import threading
from threading import Thread, Event
import cv2
import os
from IPython.display import display, Image



class RobotControl:
    def __init__(self):
        # 定义组合动作序列，每个动作增加等待时间参数（秒）
        self.motion_sequences = {
            "京族舞蹈组合": [
                ("鞠躬", "v1", 4.5),  
                ("2", "v1", 51),     
                ("3", "v1", 33),     
                ("鞠躬", "v1", 4.5)   
            ]
        }
        
        # 更新动作速度映射
        self.motion_speed = "slow"  # 可选值: "slow", "normal", "fast"
        
        # 更新单个动作的执行时间（秒）- 包含所有内置动作
        self.motion_durations = {
            "2": 51.0,
            "3": 33.0,
            "WakaWaka": 60.0,
            "LittleApple": 60.0,
            "GangnamStyle": 60.0,
            "HappyBirthday": 60.0,
            "SorrySorry": 60.0,
            "WeAreTakingOff": 60.0,
            "hengyi": 19.0
        }
        
        # 创建其他功能实例
        self.other = OtherFunctions()
        
        # 添加线程控制变量
        self.motion_thread = None
        self.stop_event = Event()
        
        self.current_volume = 50  # 默认音量值
        
        # 创建保存照片的目录
        self.photo_dir = Path("./photos")
        self.photo_dir.mkdir(exist_ok=True)
        
    def set_status_callback(self, callback):
        """设置状态更新回调函数"""
        self.other.set_status_callback(callback)
        
    def take_photo(self):
        """拍照功能
        
        Returns:
            str: 照片保存路径，失败返回None
        """
        try:
            # 先拍照
            res = YanAPI.take_vision_photo()
            if res["code"] == 0:
                # 获取照片数据并保存
                YanAPI.get_vision_photo(res["data"]["name"], str(self.photo_dir) + "/")
                photo_path = str(self.photo_dir / res["data"]["name"])
                return photo_path
            else:
                raise Exception(res["msg"])
                
        except Exception as e:
            print(f"拍照出错: {str(e)}")
            return None
    
    def start_motion(self, motion_name, version, custom_text=None):
        """执行机器人动作
        
        Args:
            motion_name (str): 动作名称
            version (str): 动作版本
            custom_text (str, optional): 对于京族舞蹈组合，可以提供自定义说话内容
        """
        try:
            # 如果已有动作在执行，先停止它
            if self.motion_thread and self.motion_thread.is_alive():
                self.stop_motion()
                time.sleep(0.5)  # 给予短暂延迟确保之前的动作已停止
            
            # 重置停止标志
            self.stop_event.clear()
            
            if motion_name in self.motion_sequences:
                # 使用线程执行合动作
                self.motion_thread = Thread(
                    target=self.play_motion_sequence,
                    args=(motion_name, custom_text)
                )
            else:
                # 使用线程执行单个动作
                self.motion_thread = Thread(
                    target=self.play_single_motion,
                    args=(motion_name, version)
                )
            
            self.motion_thread.start()
                
        except Exception as e:
            print(f"执行动作出错: {str(e)}")
            raise e
    
    def play_single_motion(self, motion_name, version):
        """在线程中执行单个动作"""
        try:
            YanAPI.start_play_motion(name=motion_name, timestamp=1, version=version)
            duration = self.motion_durations.get(motion_name, 3.0)
            
            # 使用事件等待，可以被中断
            self.stop_event.wait(timeout=duration)
            
        except Exception as e:
            print(f"执行单个动作出错: {str(e)}")
    
    def play_motion_sequence(self, sequence_name, custom_text=None):
        """在线程中执行动作序列
        
        Args:
            sequence_name (str): 动作序列名称
            custom_text (str, optional): 自定义说话内容，如果提供则使用自定义内容
        """
        if sequence_name not in self.motion_sequences:
            raise ValueError(f"未找到动作序列: {sequence_name}")
        
        # 特殊处理京族舞蹈组合，先说话再跳舞
        if sequence_name == "京族舞蹈组合":
            try:
                # 京族舞蹈介绍语，使用自定义文本或默认文本
                intro_text = custom_text if custom_text else "你好，欢迎欣赏京族传统舞蹈。京族是中国人口较少的民族之一，主要分布在广西东兴和防城港。现在我将为大家表演京族传统舞蹈，请欣赏。"
                
                print(f"机器人开始说话: {intro_text}")
                # 调用TTS接口播放介绍语
                res = YanAPI.start_voice_tts(intro_text, False)
                
                if res["code"] != 0:
                    print(f"语音播放失败: {res['msg']}")
                
                # 等待语音播放完成，这里假设每10个字需要1秒
                speech_time = len(intro_text) * 1
                time.sleep(speech_time)
                
                print("机器人开始跳舞")
            except Exception as e:
                print(f"说话功能执行出错: {str(e)}")
            
        # 执行动作序列
        sequence = self.motion_sequences[sequence_name]
        for motion_name, version, wait_time in sequence:
            # 检查是否收到停止信号
            if self.stop_event.is_set():
                break
                
            try:
                YanAPI.start_play_motion(name=motion_name, timestamp=1, version=version)
                # 使用事件等待，可以被中断
                if self.stop_event.wait(timeout=wait_time):
                    break
            except Exception as e:
                print(f"执行序列动作出错: {str(e)}")
                break
    
    def stop_motion(self):
        """停止当前动作"""
        try:
            # 设置停止标志
            self.stop_event.set()
            
            # 立即停止当前动作
            YanAPI.stop_play_motion()
            
            # 等待动作线程结束
            if self.motion_thread and self.motion_thread.is_alive():
                self.motion_thread.join(timeout=1.0)
            
            # 执行重置动作
            YanAPI.start_play_motion(name="reset", timestamp=1, version="v1")
            time.sleep(self.motion_durations.get("reset", 4.5))
            
        except Exception as e:
            print(f"停止动作出错: {str(e)}")
            raise e
    
    def reset_robot(self):
        """复位机器人"""
        try:
            # 使用 start_play_motion 来执行 reset 动作
            YanAPI.start_play_motion(name="reset", timestamp=1, version="v1")
            # 等待动作完成
            time.sleep(self.motion_durations.get("reset", 4.5))
            return {
                "code": 0,
                "msg": "复位完成"
            }
        except Exception as e:
            print(f"复位机器人出错: {str(e)}")
            raise e
    
    def get_robot_battery_info(self):
        """获取机器人电池信息
        Returns:
            Dict: {
                "code": 0,  # 0表示正常
                "data": {
                    "voltage": int,    # 电池电压(mv)
                    "charging": int,   # 充电状态(1:充电中, 0:未充电)
                    "percent": int     # 电量百分比(0-100)
                },
                "msg": str  # 提示信息
            }
        """
        try:
            return YanAPI.get_robot_battery_info()
        except Exception as e:
            return {
                "code": -1,
                "data": {
                    "voltage": 0,
                    "charging": 0,
                    "percent": 0
                },
                "msg": f"获取电池信息失败: {str(e)}"
            }
    
    def adjust_volume(self, increase=True):
        """调节机器人音量
        
        Args:
            increase (bool): True表示增加音量，False表示减小音量
        
        Returns:
            int: 调整后的音量值
        """
        try:
            # 获取当前音量
            volume_info = YanAPI.get_robot_volume()
            if volume_info["code"] == 0:
                current_volume = volume_info["data"]["volume"]
            else:
                current_volume = self.current_volume
            
            # 计算新音量值
            new_volume = current_volume + (10 if increase else -10)
            # 确保音量在有效范围内
            new_volume = max(0, min(100, new_volume))
            
            # 设置新音量
            result = YanAPI.set_robot_volume(new_volume)
            if result["code"] == 0:
                self.current_volume = new_volume
                return new_volume
            else:
                raise Exception(result["msg"])
                
        except Exception as e:
            print(f"调节音量出错: {str(e)}")
            return self.current_volume
    
    def __del__(self):
        """析构函数，确保释放摄像头"""
        self.release_camera()