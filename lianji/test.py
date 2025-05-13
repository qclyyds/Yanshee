import time
from pathlib import Path
import YanAPI
import cv2
from PIL import Image, ImageTk
import nest_asyncio
import os
import multiprocessing
import threading

# 定义机器人IP地址
ROBOT1_IP = "192.168.1.32"  # A1BB
ROBOT2_IP = "192.168.1.218"  # 97B0
ROBOT3_IP = "192.168.1.93"   # 31D1
ROBOT4_IP = "192.168.1.79"   # DAFE
ROBOT5_IP = "192.168.1.235"  # 5E1D
ROBOT6_IP = "192.168.1.40"   # E113
ROBOT7_IP = "192.168.1.91"   # 74E9
ROBOT8_IP = "192.168.1.222"  # 2478
ROBOT9_IP = "192.168.1.9"    # 6BBB
ROBOT10_IP = "192.168.1.48"  # 6660

# 初始化机器人API连接
YanAPI.yan_api_init(ROBOT1_IP)

class YansheeRobot:
    """Yanshee机器人控制类"""
    
    def __init__(self, ip):
        self.ip = ip
        YanAPI.yan_api_init(ip)
        print(f"机器人 {ip} 已初始化")
    
    def get_battery_info(self):
        """获取机器人电池信息"""
        YanAPI.yan_api_init(self.ip)  # 切换到当前机器人
        battery = YanAPI.get_robot_battery_info()
        if battery["code"] == 0:
            return battery["data"]
        else:
            return f"错误: {battery['msg']}"
    
    def set_led(self, type="button", color="blue", mode="breath"):
        """设置机器人LED灯效果"""
        YanAPI.yan_api_init(self.ip)  # 切换到当前机器人
        result = YanAPI.set_robot_led(type, color, mode)
        return result
    
    def say(self, text):
        """机器人语音播报"""
        YanAPI.yan_api_init(self.ip)  # 切换到当前机器人
        return YanAPI.sync_do_tts(text)
    
    def play_motion(self, name="reset", direction="", speed="normal", repeat=1):
        """机器人执行动作"""
        YanAPI.yan_api_init(self.ip)  # 切换到当前机器人
        return YanAPI.sync_play_motion(name, direction, speed, repeat)
    
    def volume(self, level=None):
        """获取或设置机器人音量"""
        YanAPI.yan_api_init(self.ip)  # 切换到当前机器人
        if level is None:
            return YanAPI.get_robot_volume_value()
        else:
            return YanAPI.set_robot_volume_value(level)


def robot_prepare(ip, robot_id):
    """准备阶段：连接机器人并进行初始化设置
    
    Args:
        ip: 机器人IP地址
        robot_id: 机器人ID
    
    Returns:
        YansheeRobot: 初始化后的机器人对象
    """
    robot = YansheeRobot(ip)
    print(f"机器人{robot_id}电池信息: {robot.get_battery_info()}")
    return robot


def robot_action_thread(robot, action, robot_id, barrier=None):
    """执行单个机器人动作的线程
    
    Args:
        robot: YansheeRobot实例
        action: 动作字典
        robot_id: 机器人ID
        barrier: 同步屏障
    """
    action_type = action["type"]
    
    # 如果有屏障，等待所有线程准备好
    if barrier:
        barrier.wait()
    
    # 执行动作
    if action_type == "led":
        robot.set_led(action["led_type"], action["color"], action["mode"])
        print(f"机器人{robot_id} 设置LED灯为 {action['color']}")
    elif action_type == "volume":
        robot.volume(action["level"])
        print(f"机器人{robot_id} 设置音量为 {action['level']}")
    elif action_type == "say":
        print(f"机器人{robot_id} 说: {action['text']}")
        robot.say(action["text"])
    elif action_type == "motion":
        print(f"机器人{robot_id} 执行动作: {action['name']} {action['direction']}")
        robot.play_motion(action["name"], action["direction"], 
                         action.get("speed", "normal"), 
                         action.get("repeat", 1))
    elif action_type == "wait":
        print(f"机器人{robot_id} 等待 {action['seconds']} 秒")
        time.sleep(action["seconds"])
    else:
        print(f"未知动作类型: {action_type}")


def synchronized_actions_multi(robots, actions):
    """同步执行多个机器人的动作
    
    Args:
        robots: 包含多个机器人对象的列表
        actions: 包含多个机器人动作的列表
    """
    # 创建同步屏障，数量等于机器人数量
    robot_count = len(robots)
    barrier = threading.Barrier(robot_count)
    
    # 创建多个线程分别执行机器人的动作
    threads = []
    for i, (robot, action) in enumerate(zip(robots, actions), 1):
        thread = threading.Thread(
            target=robot_action_thread, 
            args=(robot, action, i, barrier)
        )
        threads.append(thread)
    
    # 启动所有线程
    for thread in threads:
        thread.start()
    
    # 等待所有线程结束
    for thread in threads:
        thread.join()


def synchronized_actions(robot1, robot2, robot1_action, robot2_action):
    """同步执行两个机器人的动作
    
    Args:
        robot1: 第一个机器人
        robot2: 第二个机器人
        robot1_action: 第一个机器人的动作
        robot2_action: 第二个机器人的动作
    """
    # 创建同步屏障，2表示需要2个线程同时达到才能继续
    barrier = threading.Barrier(2)
    
    # 创建两个线程分别执行两个机器人的动作
    t1 = threading.Thread(target=robot_action_thread, 
                         args=(robot1, robot1_action, 1, barrier))
    t2 = threading.Thread(target=robot_action_thread, 
                         args=(robot2, robot2_action, 2, barrier))
    
    # 启动线程
    t1.start()
    t2.start()
    
    # 等待线程结束
    t1.join()
    t2.join()


def robot_process(ip, robot_id, action_queue, sync_event, sync_pairs):
    """单个机器人的控制进程
    
    Args:
        ip: 机器人IP地址
        robot_id: 机器人ID
        action_queue: 包含机器人动作的队列
        sync_event: 同步事件，用于所有进程启动时同步
        sync_pairs: 同步动作对的索引列表，表示需要与另一个机器人同步的动作
    """
    # 初始化机器人
    robot = robot_prepare(ip, robot_id)
    
    # 所有进程准备就绪，等待同步启动
    sync_event.wait()
    
    # 获取其他进程中的机器人对象，用于共享状态
    action_index = 0
    
    # 执行队列中的所有动作
    for i, action in enumerate(action_queue):
        # 检查当前动作是否需要同步
        if i in sync_pairs:
            # 等待主进程的信号，表示可以执行同步动作
            print(f"机器人{robot_id} 准备执行同步动作 {i}")
            # 这里不执行动作，而是等待主进程调用synchronized_actions函数
            sync_event.wait()
            sync_event.clear()
        else:
            # 独立执行非同步动作
            robot_action_thread(robot, action, robot_id)


def main():
    """主函数，使用多进程和线程同时控制多台机器人"""
    
    # 定义机器人的动作队列
    robot_actions = []
    
    # 机器人1的动作队列
    robot1_actions = [
        {"type": "motion", "name": "reset", "direction": ""},  # 索引0，同步
        {"type": "wait", "seconds": 1},
        {"type": "motion", "name": "LittleApple", "direction": ""}  # 索引2，同步
    ]
    robot_actions.append(robot1_actions)
    
    # 机器人2的动作队列
    robot2_actions = [
        {"type": "motion", "name": "reset", "direction": ""},  # 索引0，同步
        {"type": "wait", "seconds": 1},
        {"type": "motion", "name": "LittleApple", "direction": ""}  # 索引2，同步
    ]
    robot_actions.append(robot2_actions)
    
    # 机器人3的动作队列
    robot3_actions = [
        {"type": "motion", "name": "reset", "direction": ""},  # 索引0，同步
        {"type": "wait", "seconds": 1},
        {"type": "motion", "name": "LittleApple", "direction": ""}  # 索引2，同步
    ]
    robot_actions.append(robot3_actions)
    
    # 机器人4的动作队列
    robot4_actions = [
        {"type": "motion", "name": "reset", "direction": ""},  # 索引0，同步
        {"type": "wait", "seconds": 1},
        {"type": "motion", "name": "LittleApple", "direction": ""}  # 索引2，同步
    ]
    robot_actions.append(robot4_actions)
    
    # 机器人5的动作队列
    robot5_actions = [
        {"type": "motion", "name": "reset", "direction": ""},  # 索引0，同步
        {"type": "wait", "seconds": 1},
        {"type": "motion", "name": "LittleApple", "direction": ""}  # 索引2，同步
    ]
    robot_actions.append(robot5_actions)
    
    # 机器人6的动作队列
    robot6_actions = [
        {"type": "motion", "name": "reset", "direction": ""},  # 索引0，同步
        {"type": "wait", "seconds": 1},
        {"type": "motion", "name": "LittleApple", "direction": ""}  # 索引2，同步
    ]
    robot_actions.append(robot6_actions)
    
    # 机器人7的动作队列
    robot7_actions = [
        {"type": "motion", "name": "reset", "direction": ""},  # 索引0，同步
        {"type": "wait", "seconds": 1},
        {"type": "motion", "name": "LittleApple", "direction": ""}  # 索引2，同步
    ]
    robot_actions.append(robot7_actions)
    
    # 机器人8的动作队列
    robot8_actions = [
        {"type": "motion", "name": "reset", "direction": ""},  # 索引0，同步
        {"type": "wait", "seconds": 1},
        {"type": "motion", "name": "LittleApple", "direction": ""}  # 索引2，同步
    ]
    robot_actions.append(robot8_actions)
    
    # 机器人9的动作队列
    robot9_actions = [
        {"type": "motion", "name": "reset", "direction": ""},  # 索引0，同步
        {"type": "wait", "seconds": 1},
        {"type": "motion", "name": "LittleApple", "direction": ""}  # 索引2，同步
    ]
    robot_actions.append(robot9_actions)
    
    # 机器人10的动作队列
    robot10_actions = [
        {"type": "motion", "name": "reset", "direction": ""},  # 索引0，同步
        {"type": "wait", "seconds": 1},
        {"type": "motion", "name": "LittleApple", "direction": ""}  # 索引2，同步
    ]
    robot_actions.append(robot10_actions)
    
    # 定义需要同步的动作对的索引
    sync_pairs = [0, 2]
    
    # 准备同步事件
    sync_event = multiprocessing.Event()
    
    # 直接在主进程中创建和控制机器人
    print("初始化机器人...")
    robots = [
        robot_prepare(ROBOT1_IP, 1),
        robot_prepare(ROBOT2_IP, 2),
        robot_prepare(ROBOT3_IP, 3),
        robot_prepare(ROBOT4_IP, 4),
        robot_prepare(ROBOT5_IP, 5),
        robot_prepare(ROBOT6_IP, 6),
        robot_prepare(ROBOT7_IP, 7),
        robot_prepare(ROBOT8_IP, 8),
        robot_prepare(ROBOT9_IP, 9),
        robot_prepare(ROBOT10_IP, 10)
    ]
    
    print("启动同步控制...")
    
    # 同步执行重置动作
    print("同步执行重置动作...")
    reset_actions = [actions[0] for actions in robot_actions]
    synchronized_actions_multi(robots, reset_actions)
    
    # 等待
    time.sleep(1)
    
    # 同步执行瓦卡舞
    print("同步执行瓦卡舞...")
    waka_actions = [actions[2] for actions in robot_actions]
    synchronized_actions_multi(robots, waka_actions)
    
    print("10台机器人同步演示完成!")


if __name__ == "__main__":
    # 使用freeze_support()来支持Windows下的多进程
    multiprocessing.freeze_support()
    main()
