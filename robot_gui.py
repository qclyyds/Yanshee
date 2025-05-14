import tkinter as tk
from tkinter import ttk, messagebox
import time
from robot_control import RobotControl
from pathlib import Path
import YanAPI
import cv2
from PIL import Image, ImageTk
import nest_asyncio
import os

#初始化网络连接
#ip_addr = "192.168.110.55" 
ip_addr = "192.168.1.239"
YanAPI.yan_api_init(ip_addr)


class RobotControlGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("机器人动作控制")
        self.root.geometry("660x750")
        self.root.configure(bg='#f0f0f0')

        # 创建机器人控制实例
        self.robot = RobotControl()
        
        # 创建所有页面的容器
        self.container = tk.Frame(self.root)
        self.container.pack(side="top", fill="both", expand=True)
        
        # 创建不同的页面
        self.frames = {}
        for F in (LoginPage, MainPage, OtherFunctionsPage):
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            
        # 显示登录页面
        self.show_frame(LoginPage)
        
    def show_frame(self, cont):
        """切换到指定页面"""
        frame = self.frames[cont]
        frame.tkraise()
        # 如果是其他功能页面，确保显示内容
        if cont == OtherFunctionsPage:
            frame.show_page()
        
    def run(self):
        self.root.mainloop()

class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg='#f0f0f0')
        
        # 创建中央容器
        center_frame = tk.Frame(self, bg='#f0f0f0')
        center_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # 创建登录页面内容
        title = tk.Label(center_frame, 
                        text="京族人机",
                        font=("华文行楷", 70, "bold"),
                        bg='#f0f0f0')
        title.pack(pady=(50, 0))
        
        # 创建按钮容器
        button_frame = tk.Frame(center_frame, bg='#f0f0f0')
        button_frame.pack(pady=20)
        
        # 添加按钮
        buttons = [
            ("机器人控制", lambda: controller.show_frame(MainPage), '#2196F3'),
            ("点击开启京舞之秀", self.start_jingwu_combo, '#2196F3'),
            ("照片管理", self.show_photo_manager, '#2196F3'),
            ("关于", self.show_about, '#2196F3'),
            ("退出程序", self.exit_program, '#f44336')
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(button_frame,
                          text=text,
                          command=command,
                          width=20,
                          height=2,
                          font=("微软雅黑", 12),
                          bg=color,
                          fg='white')
            btn.pack(pady=10)
        
    def show_about(self):
        """显示关于信息"""
        about_text = """
        京族舞蹈器人

        这是一款由潘新凌，陈庆怡，马艺珉3人共同开发的专门展示京族传统舞蹈的智能机器人。通过精心编排的动作，展现京族舞蹈的优美与韵律，让更多人了解并传承京族文化艺术。

        让我们一起感受京族舞蹈的魅力！
        """
        messagebox.showinfo("关于", about_text)
        
    def exit_program(self):
        """退出程序"""
        if messagebox.askokcancel("退出", "确定要退出程序吗？"):
            self.controller.root.destroy()

    def show_photo_manager(self):
        """显示照片管理窗口"""
        photo_window = tk.Toplevel(self)
        photo_window.title("照片管理")
        photo_window.geometry("800x600")
        photo_window.configure(bg='#f0f0f0')
        
        # 创建照片列表框架
        list_frame = tk.LabelFrame(photo_window, text="照片列表", 
                                 font=("微软雅黑", 12),
                                 bg='#f0f0f0')
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # 创建照片列表
        photo_listbox = tk.Listbox(list_frame, 
                                 font=("微软雅黑", 10),
                                 selectmode=tk.SINGLE,
                                 width=50,
                                 height=15)
        photo_listbox.pack(side=tk.LEFT, fill='both', expand=True, padx=10, pady=10)
        
        # 添加滚动条
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill='y')
        
        # 配置滚动条
        photo_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=photo_listbox.yview)

        """刷新照片列表"""
        def refresh_photo_list():
            
            photo_listbox.delete(0, tk.END)
            photo_dir = Path("./photos")
            if photo_dir.exists():
                for photo in sorted(photo_dir.glob("*.jpg"), key=lambda x: x.stat().st_mtime, reverse=True):
                    photo_listbox.insert(tk.END, photo.name)
        """打开选中的照片"""
        def open_photo():
            
            selection = photo_listbox.curselection()
            if selection:
                photo_name = photo_listbox.get(selection[0])
                photo_path = Path("./photos") / photo_name
                if photo_path.exists():
                    self.show_photo(str(photo_path))
        """删除选中的照片"""
        def delete_photo():
            
            selection = photo_listbox.curselection()
            if selection:
                photo_name = photo_listbox.get(selection[0])
                photo_path = Path("./photos") / photo_name
                if messagebox.askyesno("确认删除", f"确定要删除照片 {photo_name} 吗？"):
                    try:
                        photo_path.unlink()  # 删除文件
                        refresh_photo_list()  # 刷新列表
                        messagebox.showinfo("成功", "照片已删除！")
                    except Exception as e:
                        messagebox.showerror("错误", f"删除照片时出错：{str(e)}")
        
        # 创建按钮框架
        button_frame = tk.Frame(photo_window, bg='#f0f0f0')
        button_frame.pack(pady=20)
        
        # 创建功能按钮
        buttons = [
            ("查看照片", open_photo, '#2196F3'),
            ("删除照片", delete_photo, '#f44336'),
            ("刷新列表", refresh_photo_list, '#4CAF50')
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(button_frame,
                          text=text,
                          command=command,
                          width=15,
                          height=2,
                          font=("微软雅黑", 11),
                          bg=color,
                          fg='white')
            btn.pack(side=tk.LEFT, padx=10)
        
        # 初始加载照片列表
        refresh_photo_list()

    def start_jingwu_combo(self):
        """直接执行京舞组合动作"""
        try:
            # 使用默认的说话内容执行京族舞蹈组合
            self.controller.robot.start_motion("京族舞蹈组合", "v1")
            messagebox.showinfo("成功", "京族舞蹈组合表演完成！")
        except Exception as e:
            messagebox.showerror("错误", f"执行京族舞蹈组合时出错：{str(e)}")

    def show_photo(self, photo_path):
        """显示照片"""
        try:
            # 创建窗口显示照片
            photo_window = tk.Toplevel(self)
            photo_window.title("查看照片")
            
            # 读取并调整图片大小
            image = Image.open(photo_path)
            # 计算调整后的尺寸，保持宽高比
            max_size = (800, 600)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 转换为PhotoImage对象
            photo = ImageTk.PhotoImage(image)
            
            # 创建标签显示图片
            label = tk.Label(photo_window, image=photo)
            label.image = photo  # 保持引用防止垃圾回收
            label.pack(padx=10, pady=10)
            
            # 添加关闭按钮
            close_btn = tk.Button(photo_window, 
                                text="关闭", 
                                command=photo_window.destroy,
                                font=("微软雅黑", 10),
                                bg='#f44336',
                                fg='white')
            close_btn.pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("错误", f"无法打开照片：{str(e)}")

class MainPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg='#f0f0f0')
        
        # 添加动作名称映射字典
        self.motion_name_map = {
            "瓦卡舞": "WakaWaka",
            "小苹果": "LittleApple",
            "江南Style": "GangnamStyle",
            "生日快乐": "HappyBirthday",
            "对不起对不起": "SorrySorry",
            "我们起飞啦": "WeAreTakingOff"
        }
        
        # 设置状态更新回调
        self.controller.robot.set_status_callback(self.update_status)
        
        # 创建标题标签
        self.title_label = tk.Label(self, 
                                  text="机器人动作控制",
                                  font=("微软雅黑", 20, "bold"),
                                  bg='#f0f0f0',
                                  fg='#333333')
        self.title_label.pack(pady=20)
        
        # 创建参数设置框架
        self.param_frame = tk.LabelFrame(self, text="参数设置", 
                                       font=("微软雅黑", 12),
                                       bg='#f0f0f0',
                                       padx=10, pady=10)
        self.param_frame.pack(fill='x', padx=20, pady=10)
        
        # 修改动作选择下拉框
        tk.Label(self.param_frame, text="选择动作:", 
                font=("微软雅黑", 10),
                bg='#f0f0f0').grid(row=0, column=0, pady=5, sticky='w')
        self.motion_var = tk.StringVar()
        self.motion_combo = ttk.Combobox(self.param_frame, 
                                       textvariable=self.motion_var,
                                       values=[
                                           "京族舞蹈组合",
                                           "2",
                                           "3",
                                           "瓦卡舞",
                                           "小苹果",
                                           "江南Style",
                                           "生日快乐",
                                           "对不起对不起",
                                           "我们起飞啦",
                                           "hengyi"
                                       ],
                                       width=15)
        self.motion_combo.grid(row=0, column=1, pady=5, padx=(0, 20), sticky='w')
        self.motion_combo.set("京族舞蹈组合")
        
        # 加动作说明标签
        self.motion_desc = tk.Label(self.param_frame, 
                                  text="",
                                  font=("微软雅黑", 9),
                                  bg='#f0f0f0',
                                  fg='#666666')
        self.motion_desc.grid(row=1, column=0, columnspan=2, pady=5, sticky='w')
        
        # 绑定选择事件
        self.motion_combo.bind('<<ComboboxSelected>>', self.update_motion_description)
        
        # 创建音量控制框架（放在选择动作的下方，左侧区域）
        # 音量标签和控制
        volume_label = tk.Label(self.param_frame, 
                              text="音量控制:", 
                              font=("微软雅黑", 10),
                              bg='#f0f0f0')
        volume_label.grid(row=2, column=0, pady=10, sticky='w')
        
        # 音量控制按钮框架
        volume_ctrl_frame = tk.Frame(self.param_frame, bg='#f0f0f0')
        volume_ctrl_frame.grid(row=2, column=1, pady=10, sticky='w')
        
        # 减小音量按钮
        self.volume_down_btn = tk.Button(volume_ctrl_frame,
                                       text="-",
                                       command=self.decrease_volume,
                                       width=3,
                                       font=("微软雅黑", 10),
                                       bg='#2196F3',
                                       fg='white')
        self.volume_down_btn.pack(side=tk.LEFT, padx=5)
        
        # 音量值显示标签
        self.volume_value_label = tk.Label(volume_ctrl_frame,
                                         text="50%",
                                         width=5,
                                         font=("微软雅黑", 10),
                                         bg='#f0f0f0')
        self.volume_value_label.pack(side=tk.LEFT, padx=5)
        
        # 增加音量按钮
        self.volume_up_btn = tk.Button(volume_ctrl_frame,
                                     text="+",
                                     command=self.increase_volume,
                                     width=3,
                                     font=("微软雅黑", 10),
                                     bg='#2196F3',
                                     fg='white')
        self.volume_up_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加分隔线
        ttk.Separator(self.param_frame, orient='horizontal').grid(row=3, column=0, columnspan=2, pady=10, sticky='ew')
        
        # 创建按钮框架
        self.button_frame = tk.Frame(self, bg='#f0f0f0')
        self.button_frame.pack(pady=20)
        
        # 创建功能按钮
        buttons = [
            ("开始动作", self.start_motion, '#4CAF50'),
            ("停止动作", self.stop_motion, '#f44336'),
            ("复位机器人", self.reset_robot, '#2196F3'),
            ("其他功能", self.show_other_functions, '#9C27B0')
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(self.button_frame,
                          text=text,
                          command=command,
                          width=15,
                          height=2,
                          font=("微软雅黑", 11),
                          bg=color,
                          fg='white')
            btn.pack(side=tk.LEFT, padx=10)
        
        # 在状态显示框之后添加电池信息框架
        self.battery_frame = tk.LabelFrame(self, text="电池信息", 
                                         font=("微软雅黑", 12),
                                         bg='#f0f0f0')
        self.battery_frame.pack(fill='x', padx=20, pady=10)
        
        # 创建电池信息标签
        self.battery_label = tk.Label(self.battery_frame,
                                    text="电量: --% | 状态: 未知",
                                    font=("微软雅黑", 10),
                                    bg='#f0f0f0')
        self.battery_label.pack(padx=10, pady=10)
        
        # 创建刷新电量按钮
        self.refresh_battery_btn = tk.Button(self.battery_frame,
                                           text="刷新电量",
                                           command=self.update_battery_info,
                                           font=("微软雅黑", 10),
                                           bg='#2196F3',
                                           fg='white')
        self.refresh_battery_btn.pack(pady=5)
        
        # 建状态显示框
        self.status_frame = tk.LabelFrame(self, text="状态信息", 
                                        font=("微软雅黑", 12),
                                        bg='#f0f0f0')
        self.status_frame.pack(fill='x', padx=20, pady=10)
        
        self.status_text = tk.Text(self.status_frame, height=6, width=50)
        self.status_text.pack(padx=10, pady=10)
        
        # 添加返回登录页面的按钮
        self.back_button = tk.Button(self,
                                   text="返回",
                                   command=lambda: controller.show_frame(LoginPage),
                                   font=("微软雅黑", 14))
        self.back_button.pack(pady=14)
        
        # 初始获取电量信息
        self.update_battery_info()
        
        # 在创建完音量控制界面后，添加初始化音量显示
        self.init_volume_display()
        
    def init_volume_display(self):
        """初始化音量显示"""
        try:
            # 获取当前音量
            volume_info = YanAPI.get_robot_volume()
            if volume_info["code"] == 0:
                current_volume = volume_info["data"]["volume"]
                # 更新显示
                self.volume_value_label.config(text=f"{current_volume}%")
                self.update_status(f"当前音量: {current_volume}%")
            else:
                raise Exception(volume_info["msg"])
        except Exception as e:
            error_msg = f"获取音量信息失败: {str(e)}"
            self.update_status(error_msg)
            self.volume_value_label.config(text="---%")
#--------------------------------------参数--------------------------------------
    def update_status(self, message):
        self.status_text.insert('end', f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.status_text.see('end')
        
    def start_motion(self):
        """执行机器人动作"""
        try:
            motion_name = self.motion_var.get()
            
            custom_text = None
            if motion_name == "京族舞蹈组合":
                self.update_status(f"开始执行：先说话后跳京族舞蹈")
            
            # 如果选择的是映射中的中文名称，转换为英文名称
            if motion_name in self.motion_name_map:
                motion_name = self.motion_name_map[motion_name]
                
            self.update_status(f"开始执行动作: {self.motion_var.get()}")
            self.controller.robot.start_motion(motion_name, "v1", custom_text)
            self.update_status("动作执行完成！")
        except Exception as e:
            error_msg = f"执行动作时出错：{str(e)}"
            self.update_status(error_msg)
            messagebox.showerror("错误", error_msg)
            
    def stop_motion(self):
        try:
            self.controller.robot.stop_motion()
            self.update_status("动作已停止")
        except Exception as e:
            self.update_status(f"停止动作时出错：{str(e)}")
            
    def reset_robot(self):
        """复位机器人"""
        # 调用 RobotControl 中 reset_robot 方法
        self.controller.robot.reset_robot()
        self.update_status("机器人复位完成！")
        
            
    def show_other_functions(self):
        """显示其他功能页面"""
        # 切换到其他功能页面
        self.controller.show_frame(OtherFunctionsPage)
        # 获取其他功能页面实例并调用show_page方法
        other_page = self.controller.frames[OtherFunctionsPage]
        other_page.show_page()
    
    def update_battery_info(self):
        """更新电池信息显示"""
        try:
            battery_info = self.controller.robot.get_robot_battery_info()
            if battery_info["code"] == 0:
                data = battery_info["data"]
                percent = data["percent"]
                charging = "充电中" if data["charging"] == 1 else "未充电"
                voltage = data["voltage"]
                
                self.battery_label.config(
                    text=f"电量: {percent}% | 状态: {charging} | 电压: {voltage}mv"
                )
                
                # 根据电量设置不同的颜色
                if percent <= 20:
                    self.battery_label.config(fg='red')
                elif percent <= 50:
                    self.battery_label.config(fg='orange')
                else:
                    self.battery_label.config(fg='green')
                    
            else:
                self.battery_label.config(text="获取电量信息失败")
                self.update_status("获取电量信息失败")
        except Exception as e:
            error_msg = f"获取电量信息出错：{str(e)}"
            self.update_status(error_msg)
            self.battery_label.config(text="获取电量信息出错")

    def update_motion_description(self, event=None):
        """更新动作说明"""
        motion_descriptions = {
            "京族舞蹈组合": "完整的京族舞蹈表演组合",
            "2": "京族舞蹈组合",
            "3": "京族舞蹈组合",
            "鞠躬": "机器人鞠躬动作"
        }
        
        selected_motion = self.motion_var.get()
        description = motion_descriptions.get(selected_motion, "")
        self.motion_desc.config(text=description)

    def increase_volume(self):
        """增加音量"""
        try:
            new_volume = self.controller.robot.adjust_volume(increase=True)
            self.volume_value_label.config(text=f"{new_volume}%")
            self.update_status(f"音量已调整为 {new_volume}%")
        except Exception as e:
            self.update_status(f"调节音量失败: {str(e)}")
    
    def decrease_volume(self):
        """减小音量"""
        try:
            new_volume = self.controller.robot.adjust_volume(increase=False)
            self.volume_value_label.config(text=f"{new_volume}%")
            self.update_status(f"音量已调整为 {new_volume}%")
        except Exception as e:
            self.update_status(f"调节音量失败: {str(e)}")

class OtherFunctionsPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg='#f0f0f0')
        
    def show_page(self):
        """显示其他功能主页面"""
        # 清空当前页面的所有控件
        for widget in self.winfo_children():
            widget.destroy()
            
        # 创建标题
        title_label = tk.Label(self,
                             text="其他功能",
                             font=("微软雅黑", 20, "bold"),
                             bg='#f0f0f0')
        title_label.pack(pady=20)
        
        # 创建按钮框架
        button_frame = tk.Frame(self, bg='#f0f0f0')
        button_frame.pack(expand=True)
        
        # 创建功能按钮
        buttons = [
            ("拍照", self.show_photo_page, '#2196F3'),
            ("实时监控", self.show_monitor_page, '#9C27B0'),
            ("语音交互", self.show_voice_page, '#FF9800'),  # 新增语音交互按钮
            ("返回", lambda: self.controller.show_frame(MainPage), '#f44336')
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(button_frame,
                          text=text,
                          command=command,
                          width=15,
                          height=2,
                          font=("微软雅黑", 11),
                          bg=color,
                          fg='white')
            btn.pack(pady=10)
            
    def show_monitor_page(self):
        """显示实时监控页面"""
        # 清空当前页面
        for widget in self.winfo_children():
            widget.destroy()
            
        # 创建标题
        title_label = tk.Label(self,
                             text="实时监控",
                             font=("微软雅黑", 20, "bold"),
                             bg='#f0f0f0')
        title_label.pack(pady=20)
        
        # 创建状态标签
        self.monitor_status_label = tk.Label(self,
                                           text="点击开始按钮启动实时监控",
                                           font=("微软雅黑", 12),
                                           bg='#f0f0f0')
        self.monitor_status_label.pack(pady=10)
        
        # 创建视觉模式选择框架
        mode_frame = tk.LabelFrame(self, 
                                 text="视觉模式选择",
                                 font=("微软雅黑", 12),
                                 bg='#f0f0f0')
        mode_frame.pack(pady=10, padx=20, fill='x')
        
        # 创建一个内部框架用于居中按钮
        center_frame = tk.Frame(mode_frame, bg='#f0f0f0')
        center_frame.pack(expand=True)
        
        # 创建视觉模式按钮
        modes = [
            ("人脸识别", "人脸识别", '#2196F3'),
            ("人脸分析", "人脸分析", '#4CAF50'),
            ("颜色检测", "颜色检测", '#FF9800'),
            ("物体识别", "物体识别", '#9C27B0'),
            ("手势识别", "手势识别", '#E91E63'),
        ]
        
        # 竖向排列模式按钮
        for text, mode, color in modes:
            btn = tk.Button(center_frame,
                          text=text,
                          command=lambda m=mode: self.change_vision_mode(m),
                          width=15,
                          height=2,
                          font=("微软雅黑", 11),
                          bg=color,
                          fg='white')
            btn.pack(pady=5)  # 只使用垂直间距
        
        # 创建控制按钮框架
        button_frame = tk.Frame(self, bg='#f0f0f0')
        button_frame.pack(pady=20)
        
        # 创建控制按钮
        buttons = [
            ("开始监控", self.start_monitor, '#4CAF50'),
            ("返回", self.show_page, '#f44336')
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(button_frame,
                          text=text,
                          command=command,
                          width=15,
                          height=2,
                          font=("微软雅黑", 11),
                          bg=color,
                          fg='white')
            btn.pack(side=tk.LEFT, padx=10)
            
    def change_vision_mode(self, mode_name):
        """切换视觉模式"""
        try:
            self.controller.robot.other.change_vision_mode(mode_name)
            self.monitor_status_label.config(text=f"已切换到{mode_name}模式")
        except Exception as e:
            error_msg = f"切换视觉模式失败：{str(e)}"
            self.monitor_status_label.config(text=error_msg)
            messagebox.showerror("错误", error_msg)
            
    def start_monitor(self):
        """开始实时监控"""
        try:
            if self.controller.robot.other.show_monitor():
                self.monitor_status_label.config(text="实时监控已启动")
            else:
                raise Exception("启动监控失败")
        except Exception as e:
            error_msg = f"启动监控失败：{str(e)}"
            self.monitor_status_label.config(text=error_msg)
            messagebox.showerror("错误", error_msg)

    def show_photo_page(self):
        """显示拍照页面"""
        # 清空当前页面
        for widget in self.winfo_children():
            widget.destroy()
            
        # 创建标题
        title_label = tk.Label(self,
                             text="拍照功能",
                             font=("微软雅黑", 20, "bold"),
                             bg='#f0f0f0')
        title_label.pack(pady=20)
        
        # 创建状态标签
        self.photo_status_label = tk.Label(self,
                                         text="点击拍照按钮开始拍照",
                                         font=("微软雅黑", 12),
                                         bg='#f0f0f0')
        self.photo_status_label.pack(pady=10)
        
        # 创建照片预览框架
        preview_frame = tk.LabelFrame(self,
                                    text="照片预览",
                                    font=("微软雅黑", 12),
                                    bg='#f0f0f0')
        preview_frame.pack(pady=10, padx=20)
        
        # 创建照片预览标签
        self.preview_label = tk.Label(preview_frame, bg='#ffffff')
        self.preview_label.pack(padx=10, pady=10)
        
        # 创建按钮框架
        button_frame = tk.Frame(self, bg='#f0f0f0')
        button_frame.pack(pady=20)
        
        # 创建功能按钮
        buttons = [
            ("拍照", self.take_photo, '#4CAF50'),
            ("返回", self.show_page, '#f44336')
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(button_frame,
                          text=text,
                          command=command,
                          width=15,
                          height=2,
                          font=("微软雅黑", 11),
                          bg=color,
                          fg='white')
            btn.pack(side=tk.LEFT, padx=10)
            
    def take_photo(self):
        """拍照功能"""
        try:
            photo_path = self.controller.robot.take_photo()
            if photo_path:
                self.photo_status_label.config(text=f"照片已保存至: {photo_path}")
                # 显示预览图
                self.show_preview(photo_path)
            else:
                raise Exception("拍照失败")
        except Exception as e:
            error_msg = f"拍照出错：{str(e)}"
            self.photo_status_label.config(text=error_msg)
            messagebox.showerror("错误", error_msg)
            
    def show_preview(self, photo_path):
        """显示照片预览"""
        try:
            # 读取图片
            image = Image.open(photo_path)
            
            # 计算调整后的尺寸，保持宽高比
            # 设置预览框的最大尺寸
            max_size = (400, 300)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 转换为PhotoImage对象
            photo = ImageTk.PhotoImage(image)
            
            # 更新预览标签
            self.preview_label.config(image=photo)
            self.preview_label.image = photo  # 保持引用防止垃圾回收
            
        except Exception as e:
            error_msg = f"显示预览图失败：{str(e)}"
            self.photo_status_label.config(text=error_msg)
            messagebox.showerror("错误", error_msg)

    def show_voice_page(self):
        """显示语音交互主页面"""
        # 清空当前页面
        for widget in self.winfo_children():
            widget.destroy()
            
        # 创建标题
        title_label = tk.Label(self,
                             text="语音交互",
                             font=("微软雅黑", 20, "bold"),
                             bg='#f0f0f0')
        title_label.pack(pady=20)
        
        # 创建功能选择框架
        function_frame = tk.LabelFrame(self, 
                                     text="功能选择",
                                     font=("微软雅黑", 12),
                                     bg='#f0f0f0')
        function_frame.pack(pady=10, padx=20, fill='x')
        
        # 创建功能按钮
        functions = [
            ("语音转文本", self.show_voice_to_text_page, '#2196F3'),
            ("文本转语音", self.show_text_to_speech_page, '#4CAF50'),
            ("语义理解", self.show_voice_nlp_page, '#FF9800'),  # 新增语义理解按钮
        ]
        
        # 使用网格布局排列功能按钮
        for i, (text, command, color) in enumerate(functions):
            btn = tk.Button(function_frame,
                          text=text,
                          command=command,
                          width=15,
                          height=2,
                          font=("微软雅黑", 11),
                          bg=color,
                          fg='white')
            btn.pack(pady=10)
        
        # 创建控制按钮框架
        button_frame = tk.Frame(self, bg='#f0f0f0')
        button_frame.pack(pady=20)
        
        # 创建返回按钮
        tk.Button(button_frame,
                 text="返回",
                 command=self.show_page,
                 width=15,
                 height=2,
                 font=("微软雅黑", 11),
                 bg='#f44336',
                 fg='white').pack()

    def show_voice_to_text_page(self):
        """显示语音转文本页面"""
        # 清空当前页面
        for widget in self.winfo_children():
            widget.destroy()
            
        # 创建标题
        title_label = tk.Label(self,
                             text="语音转文本",
                             font=("微软雅黑", 20, "bold"),
                             bg='#f0f0f0')
        title_label.pack(pady=20)
        
        # 创建状态显示框架
        status_frame = tk.LabelFrame(self,
                                   text="识别状态",
                                   font=("微软雅黑", 12),
                                   bg='#f0f0f0')
        status_frame.pack(pady=10, padx=20, fill='x')
        
        # 创建状态文本框
        self.voice_status_text = tk.Text(status_frame, 
                                       height=10, 
                                       width=50,
                                       font=("微软雅黑", 10))
        self.voice_status_text.pack(padx=10, pady=10)
        
        # 设置语音识别状态回调
        self.controller.robot.other.set_voice_callback(self.update_voice_status)
        
        # 创建按钮框架
        button_frame = tk.Frame(self, bg='#f0f0f0')
        button_frame.pack(pady=20)
        
        # 创建功能按钮
        buttons = [
            ("开始识别", self.start_voice_recognition, '#4CAF50'),
            ("返回", self.show_voice_page, '#f44336')  # 注意这里返回到语音交互主页面
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(button_frame,
                          text=text,
                          command=command,
                          width=15,
                          height=2,
                          font=("微软雅黑", 11),
                          bg=color,
                          fg='white')
            btn.pack(side=tk.LEFT, padx=10)
            
    def start_voice_recognition(self):
        """开始语音识别"""
        try:
            self.update_voice_status("开始语音识别...")
            success, result = self.controller.robot.other.voice_to_text()
            if success:
                self.update_voice_status(f"识别成功：{result}")
            else:
                self.update_voice_status(f"识别失败：{result}")
        except Exception as e:
            self.update_voice_status(f"识别出错：{str(e)}")
            
    def update_voice_status(self, message):
        """更新语音识别状态"""
        self.voice_status_text.insert('end', f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.voice_status_text.see('end')

    def show_text_to_speech_page(self):
        """显示文本转语音页面"""
        # 清空当前页面
        for widget in self.winfo_children():
            widget.destroy()
            
        # 创建标题
        title_label = tk.Label(self,
                             text="文本转语音",
                             font=("微软雅黑", 20, "bold"),
                             bg='#f0f0f0')
        title_label.pack(pady=20)
        
        # 创建文本输入框架
        input_frame = tk.LabelFrame(self,
                                  text="输入文本",
                                  font=("微软雅黑", 12),
                                  bg='#f0f0f0')
        input_frame.pack(pady=10, padx=20, fill='x')
        
        # 创建文本输入框
        self.text_input = tk.Text(input_frame,
                                height=5,
                                width=50,
                                font=("微软雅黑", 10))
        self.text_input.pack(padx=10, pady=10)
        self.text_input.insert('1.0', "你好，我是智能教育机器人Yanshee")
        
        # 创建状态显示框架
        status_frame = tk.LabelFrame(self,
                                   text="播放状态",
                                   font=("微软雅黑", 12),
                                   bg='#f0f0f0')
        status_frame.pack(pady=10, padx=20, fill='x')
        
        # 创建状态文本框
        self.tts_status_text = tk.Text(status_frame,
                                     height=5,
                                     width=50,
                                     font=("微软雅黑", 10))
        self.tts_status_text.pack(padx=10, pady=10)
        
        # 设置语音回调
        self.controller.robot.other.set_voice_callback(self.update_tts_status)
        
        # 创建按钮框架
        button_frame = tk.Frame(self, bg='#f0f0f0')
        button_frame.pack(pady=20)
        
        # 创建功能按钮
        buttons = [
            ("开始播放", self.start_speech, '#4CAF50'),
            ("停止播放", self.stop_speech, '#FF5722'),
            ("返回", self.show_voice_page, '#f44336')
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(button_frame,
                          text=text,
                          command=command,
                          width=15,
                          height=2,
                          font=("微软雅黑", 11),
                          bg=color,
                          fg='white')
            btn.pack(side=tk.LEFT, padx=10)
            
    def start_speech(self):
        """开始语音播放"""
        try:
            text = self.text_input.get('1.0', 'end-1c')
            if not text.strip():
                raise Exception("请输入要播放的文本")
                
            success, result = self.controller.robot.other.text_to_speech(text)
            if not success:
                raise Exception(result)
                
        except Exception as e:
            self.update_tts_status(f"播放出错：{str(e)}")
            messagebox.showerror("错误", str(e))
            
    def stop_speech(self):
        """停止语音播放"""
        try:
            success, result = self.controller.robot.other.stop_speech()
            if not success:
                raise Exception(result)
                
        except Exception as e:
            self.update_tts_status(f"停止播放出错：{str(e)}")
            messagebox.showerror("错误", str(e))
            
    def update_tts_status(self, message):
        """更新语音播放状态"""
        self.tts_status_text.insert('end', f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.tts_status_text.see('end')

    def show_voice_nlp_page(self):
        """显示语义理解页面"""
        # 清空当前页面
        for widget in self.winfo_children():
            widget.destroy()
            
        # 创建标题
        title_label = tk.Label(self,
                             text="语义理解",
                             font=("微软雅黑", 20, "bold"),
                             bg='#f0f0f0')
        title_label.pack(pady=20)
        
        # 创建状态显示框架
        status_frame = tk.LabelFrame(self,
                                   text="对话记录",
                                   font=("微软雅黑", 12),
                                   bg='#f0f0f0')
        status_frame.pack(pady=10, padx=20, fill='x')
        
        # 创建状态文本框
        self.nlp_status_text = tk.Text(status_frame, 
                                     height=10, 
                                     width=50,
                                     font=("微软雅黑", 10))
        self.nlp_status_text.pack(padx=10, pady=10)
        
        # 设置语音识别状态回调
        self.controller.robot.other.set_voice_callback(self.update_nlp_status)
        
        # 创建按钮框架
        button_frame = tk.Frame(self, bg='#f0f0f0')
        button_frame.pack(pady=20)
        
        # 创建功能按钮
        buttons = [
            ("开始对话", self.start_nlp_dialog, '#4CAF50'),
            ("返回", self.show_voice_page, '#f44336')
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(button_frame,
                          text=text,
                          command=command,
                          width=15,
                          height=2,
                          font=("微软雅黑", 11),
                          bg=color,
                          fg='white')
            btn.pack(side=tk.LEFT, padx=10)
            
    def start_nlp_dialog(self):
        """开始语义理解对话"""
        try:
            self.update_nlp_status("请开始说话...")
            success, result = self.controller.robot.other.voice_to_nlp()
            if success:
                # 自动播放回答
                self.controller.robot.other.text_to_speech(result)
            else:
                self.update_nlp_status(f"对话失败：{result}")
        except Exception as e:
            self.update_nlp_status(f"对话出错：{str(e)}")
            
    def update_nlp_status(self, message):
        """更新语义理解状态"""
        self.nlp_status_text.insert('end', f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.nlp_status_text.see('end')

if __name__ == "__main__":
    app = RobotControlGUI()
    app.run() 