import YanAPI
import time
from pathlib import Path
import json
import requests
import cv2
from IPython.display import display, Image
ip_addr = "192.168.110.55" # please change to your yanshee robot IP
YanAPI.yan_api_init(ip_addr)

class OtherFunctions:
    def __init__(self):
        # 创建保存照片的目录
        self.photo_dir = Path("./photos")
        self.photo_dir.mkdir(exist_ok=True)
        
        # 状态更新回调函数
        self.status_callback = None
        
        # 监控窗口状态
        self.monitor_running = False
        
        # 添加视觉模式列表
        self.vision_modes = {
            "人脸识别": "face_recognition_remote",
            "人脸分析": "face_attribute_remote",
            "颜色检测": "color_detect_remote",
            "物体识别": "object_recognition_remote",
            "手势识别": "gesture_recognition_remote",
        }
        
        # 当前视觉模式
        self.current_mode = "face_attribute_remote"
        
        # 添加语音识别状态回调
        self.voice_callback = None
        
        # 默认TTS文本
        self.default_tts_text = "你好，我是智能教育机器人Yanshee"
        
    def set_status_callback(self, callback):
        """设置状态更新回调函数"""
        self.status_callback = callback
        
    def update_status(self, message):
        """更新状态信息"""
        if self.status_callback:
            self.status_callback(message)
            
        
    def show_monitor(self):
        """显示实时监控"""
        try:
            self.monitor_running = True
            YanAPI.show_visions_result(self.current_mode)
            return True
        except Exception as e:
            print(f"启动实时监控失败: {str(e)}")
            return False
            
    def change_vision_mode(self, mode_name):
        """切换视觉模式
        
        Args:
            mode_name (str): 模式名称（中文）
        """
        if mode_name in self.vision_modes:
            self.current_mode = self.vision_modes[mode_name]
            self.update_status(f"已切换到{mode_name}模式")
            # 重新启动监控以应用新模式
            if self.monitor_running:
                self.show_monitor()

    def voice_to_text(self):
        """语音转文本功能
        
        Returns:
            tuple: (是否成功, 识别结果文本)
        """
        try:
            # 调用语音转文本服务接口
            res = YanAPI.sync_do_voice_iat()
            
            # 更新状态
            if self.voice_callback:
                self.voice_callback("正在识别语音...")
            
            # 解析结果
            if res["code"] == 0 and len(res["data"]) > 0:
                words = res["data"]["text"]['ws']
                result = ""
                for word in words:
                    result += word['cw'][0]['w']
                    
                if self.voice_callback:
                    self.voice_callback(f"识别结果：{result}")
                return True, result
            else:
                if self.voice_callback:
                    self.voice_callback("没有听到说话")
                return False, "没有听到说话"
                
        except Exception as e:
            error_msg = f"语音识别失败：{str(e)}"
            if self.voice_callback:
                self.voice_callback(error_msg)
            return False, error_msg
            
    def set_voice_callback(self, callback):
        """设置语音识别状态回调"""
        self.voice_callback = callback

    def voice_to_nlp(self):
        """语义理解功能
        
        Returns:
            tuple: (是否成功, 理解结果文本)
        """
        try:
            # 调用语义理解接口
            res = YanAPI.sync_do_voice_asr()
            
            # 更新状态
            if self.voice_callback:
                self.voice_callback("正在进行语义理解...")
            
            # 解析结果
            if res["code"] == 0 and len(res["data"]) > 0:
                answer = res["data"]['intent']['answer']['text']
                
                if self.voice_callback:
                    self.voice_callback(f"机器人回复：{answer}")
                return True, answer
            else:
                if self.voice_callback:
                    self.voice_callback("没有听到说话")
                return False, "没有听到说话"
                
        except Exception as e:
            error_msg = f"语义理解失败：{str(e)}"
            if self.voice_callback:
                self.voice_callback(error_msg)
            return False, error_msg

    def text_to_speech(self, text=None, can_interrupt=True):
        """文本转语音功能
        
        Args:
            text (str, optional): 要播放的文本. 默认为None，使用默认文本
            can_interrupt (bool, optional): 是否允许打断. 默认为True
            
        Returns:
            tuple: (是否成功, 结果信息)
        """
        try:
            # 如果没有提供文本，使用默认文本
            if text is None:
                text = self.default_tts_text
                
            # 更新状态
            if self.voice_callback:
                self.voice_callback(f"正在播放：{text}")
            
            # 调用TTS接口
            res = YanAPI.start_voice_tts(text, can_interrupt)
            
            if res["code"] == 0:
                return True, "播放成功"
            else:
                raise Exception(res["msg"])
                
        except Exception as e:
            error_msg = f"语音播放失败：{str(e)}"
            if self.voice_callback:
                self.voice_callback(error_msg)
            return False, error_msg
            
    def stop_speech(self):
        """停止语音播放
        
        Returns:
            tuple: (是否成功, 结果信息)
        """
        try:
            res = YanAPI.stop_voice_tts()
            
            if res["code"] == 0:
                if self.voice_callback:
                    self.voice_callback("语音播放已停止")
                return True, "停止成功"
            else:
                raise Exception(res["msg"])
                
        except Exception as e:
            error_msg = f"停止语音失败：{str(e)}"
            if self.voice_callback:
                self.voice_callback(error_msg)
            return False, error_msg
