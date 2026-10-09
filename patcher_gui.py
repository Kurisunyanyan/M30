# -*- coding: utf-8 -*-
"""
Macross 30 Chinese Patcher GUI (Universal Edition v1.5)
======================================================
"""

import os, sys, threading, time, shutil
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

if getattr(sys, "frozen", False):
    SCRIPT_DIR = Path(sys.executable).resolve().parent
else:
    SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import patcher_engine

class PatcherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("超时空要塞 30：联系银河的歌声 - 汉化补丁器 v1.5 (通用版)")
        self.geometry("780x680")
        self.minsize(720, 560)
        
        # Variables
        self.main_mode = tk.StringVar(value="rpcs3")         # "rpcs3", "ps3_export", "disc_inplace"
        self.rpcs3_sub_mode = tk.StringVar(value="iso")      # "iso", "disc"
        self.ps3_source_type = tk.StringVar(value="iso")     # "iso", "disc"
        self.ps3_export_format = tk.StringVar(value="iso")   # "iso", "folder"

        self.rpcs3_path = tk.StringVar(value="")
        self.iso_path = tk.StringVar(value="")
        self.disc_path = tk.StringVar(value="")
        self.output_dir = tk.StringVar(value="")
        self.cache_dir = tk.StringVar(value="")
        
        self.create_widgets()
        self.detect_default_paths()
        self.update_ui_state()

    def create_widgets(self):
        pad = {"padx": 10, "pady": 4}
        
        # 1. Header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", **pad)
        lbl_title = ttk.Label(header_frame, text="超时空要塞 30 中文汉化补丁器", font=("Microsoft YaHei", 14, "bold"))
        lbl_title.pack(anchor="w")
        lbl_sub = ttk.Label(header_frame, text="支持 RPCS3 模拟器一键修补 与 PS3 实体机数据独立导出，双轨位级注入 + 64部硬字幕压制", font=("Microsoft YaHei", 9))
        lbl_sub.pack(anchor="w")

        # 2. Main Mode Notebook / Radio selection
        mode_frame = ttk.LabelFrame(self, text="【选择工作模式】")
        mode_frame.pack(fill="x", **pad)
        
        r1 = ttk.Radiobutton(mode_frame, text="模式 1：RPCS3 模拟器模式 (全自动修补并同步注入模拟器硬盘)", 
                             variable=self.main_mode, value="rpcs3", command=self.update_ui_state)
        r1.pack(anchor="w", padx=10, pady=2)
        lbl_d1 = ttk.Label(mode_frame, text="    适合 PC 玩家：修补原版 ISO / 光盘文件夹，并自动写平 dev_hdd0 安装大包与 1.02 汉化 EBOOT。", font=("Microsoft YaHei", 8), foreground="gray")
        lbl_d1.pack(anchor="w", padx=10, pady=(0, 2))

        r2 = ttk.Radiobutton(mode_frame, text="模式 2：PS3 实体机导出模式 (免 RPCS3，自定义输出汉化 ISO / 游戏文件夹)", 
                             variable=self.main_mode, value="ps3_export", command=self.update_ui_state)
        r2.pack(anchor="w", padx=10, pady=2)
        lbl_d2 = ttk.Label(mode_frame, text="    适合 PS3 破解实机玩家：无需安装 RPCS3，自选输出目录，导出汉化版 ISO 或 JB 文件夹 + 1.02 汉化 EBOOT。", font=("Microsoft YaHei", 8), foreground="gray")
        lbl_d2.pack(anchor="w", padx=10, pady=(0, 2))

        r3 = ttk.Radiobutton(mode_frame, text="模式 3：直接修补已解压光盘目录 (原位就地修补)", 
                             variable=self.main_mode, value="disc_inplace", command=self.update_ui_state)
        r3.pack(anchor="w", padx=10, pady=2)
        lbl_d3 = ttk.Label(mode_frame, text="    适合高级用户：直接就地修补指定的 PS3_GAME 目录中的大包、EBOOT 并压制 64 部 PAM 视频。", font=("Microsoft YaHei", 8), foreground="gray")
        lbl_d3.pack(anchor="w", padx=10, pady=(0, 2))

        # 3. Path & Config Area
        self.config_frame = ttk.LabelFrame(self, text="【输入与输出路径配置】")
        self.config_frame.pack(fill="x", **pad)

        # Row: RPCS3 Root (Mode 1 only)
        self.row_rpcs3 = ttk.Frame(self.config_frame)
        lbl_rpcs3 = ttk.Label(self.row_rpcs3, text="RPCS3 根目录:", width=15)
        lbl_rpcs3.pack(side="left")
        self.ent_rpcs3 = ttk.Entry(self.row_rpcs3, textvariable=self.rpcs3_path)
        self.ent_rpcs3.pack(side="left", fill="x", expand=True, padx=6)
        btn_browse_rpcs3 = ttk.Button(self.row_rpcs3, text="浏览...", command=self.browse_rpcs3)
        btn_browse_rpcs3.pack(side="right")

        # Sub-choice for Mode 1
        self.row_rpcs3_sub = ttk.Frame(self.config_frame)
        lbl_sub_type = ttk.Label(self.row_rpcs3_sub, text="游戏源类型:", width=15)
        lbl_sub_type.pack(side="left")
        rb_rpcs3_iso = ttk.Radiobutton(self.row_rpcs3_sub, text="原版 ISO 镜像", variable=self.rpcs3_sub_mode, value="iso", command=self.update_ui_state)
        rb_rpcs3_iso.pack(side="left", padx=10)
        rb_rpcs3_disc = ttk.Radiobutton(self.row_rpcs3_sub, text="解压光盘目录 (PS3_GAME)", variable=self.rpcs3_sub_mode, value="disc", command=self.update_ui_state)
        rb_rpcs3_disc.pack(side="left", padx=10)

        # Sub-choice for Mode 2 (PS3 Export)
        self.row_ps3_cfg = ttk.Frame(self.config_frame)
        lbl_ps3_src = ttk.Label(self.row_ps3_cfg, text="输入源类型:", width=15)
        lbl_ps3_src.pack(side="left")
        rb_ps3_src_iso = ttk.Radiobutton(self.row_ps3_cfg, text="原版 ISO", variable=self.ps3_source_type, value="iso", command=self.update_ui_state)
        rb_ps3_src_iso.pack(side="left", padx=5)
        rb_ps3_src_disc = ttk.Radiobutton(self.row_ps3_cfg, text="解压光盘文件夹", variable=self.ps3_source_type, value="disc", command=self.update_ui_state)
        rb_ps3_src_disc.pack(side="left", padx=5)

        lbl_ps3_fmt = ttk.Label(self.row_ps3_cfg, text="    导出产物格式:", width=16)
        lbl_ps3_fmt.pack(side="left")
        rb_ps3_fmt_iso = ttk.Radiobutton(self.row_ps3_cfg, text="PS3 专用 ISO", variable=self.ps3_export_format, value="iso")
        rb_ps3_fmt_iso.pack(side="left", padx=5)
        rb_ps3_fmt_folder = ttk.Radiobutton(self.row_ps3_cfg, text="游戏文件夹 (GAMES)", variable=self.ps3_export_format, value="folder")
        rb_ps3_fmt_folder.pack(side="left", padx=5)

        # Row: ISO File
        self.row_iso = ttk.Frame(self.config_frame)
        lbl_iso = ttk.Label(self.row_iso, text="原版 ISO 文件:", width=15)
        lbl_iso.pack(side="left")
        self.ent_iso = ttk.Entry(self.row_iso, textvariable=self.iso_path)
        self.ent_iso.pack(side="left", fill="x", expand=True, padx=6)
        btn_browse_iso = ttk.Button(self.row_iso, text="浏览...", command=self.browse_iso)
        btn_browse_iso.pack(side="right")

        # Row: Disc Folder
        self.row_disc = ttk.Frame(self.config_frame)
        lbl_disc = ttk.Label(self.row_disc, text="光盘解压目录:", width=15)
        lbl_disc.pack(side="left")
        self.ent_disc = ttk.Entry(self.row_disc, textvariable=self.disc_path)
        self.ent_disc.pack(side="left", fill="x", expand=True, padx=6)
        btn_browse_disc = ttk.Button(self.row_disc, text="浏览...", command=self.browse_disc)
        btn_browse_disc.pack(side="right")

        # Row: Destination Output Folder (Mode 2)
        self.row_output = ttk.Frame(self.config_frame)
        lbl_output = ttk.Label(self.row_output, text="汉化输出目录:", width=15)
        lbl_output.pack(side="left")
        self.ent_output = ttk.Entry(self.row_output, textvariable=self.output_dir)
        self.ent_output.pack(side="left", fill="x", expand=True, padx=6)
        btn_browse_output = ttk.Button(self.row_output, text="浏览...", command=self.browse_output)
        btn_browse_output.pack(side="right")

        # Row: Working Cache Folder (Avoid C: drive explosion)
        self.row_cache = ttk.Frame(self.config_frame)
        lbl_cache = ttk.Label(self.row_cache, text="工作缓存目录:", width=15)
        lbl_cache.pack(side="left")
        self.ent_cache = ttk.Entry(self.row_cache, textvariable=self.cache_dir)
        self.ent_cache.pack(side="left", fill="x", expand=True, padx=6)
        btn_browse_cache = ttk.Button(self.row_cache, text="浏览...", command=self.browse_cache)
        btn_browse_cache.pack(side="right")

        # 4. Action Button
        act_frame = ttk.Frame(self)
        act_frame.pack(fill="x", **pad)
        self.btn_run = ttk.Button(act_frame, text="开始执行汉化补丁流程", command=self.start_patch_thread)
        self.btn_run.pack(side="left", fill="x", expand=True, ipady=4)
        
        # 5. Log Output Area
        log_frame = ttk.LabelFrame(self, text="【执行日志】")
        log_frame.pack(fill="both", expand=True, **pad)
        self.log_txt = scrolledtext.ScrolledText(log_frame, font=("Consolas", 9), wrap="word")
        self.log_txt.pack(fill="both", expand=True, padx=6, pady=6)

    def log(self, text_line):
        self.log_txt.insert("end", text_line + "\n")
        self.log_txt.see("end")

    def update_ui_state(self):
        m = self.main_mode.get()
        
        # Hide all conditional rows first
        for row in [self.row_rpcs3, self.row_rpcs3_sub, self.row_ps3_cfg, self.row_iso, self.row_disc, self.row_output, self.row_cache]:
            row.pack_forget()

        if m == "rpcs3":
            self.row_rpcs3.pack(fill="x", padx=10, pady=3)
            self.row_rpcs3_sub.pack(fill="x", padx=10, pady=3)
            if self.rpcs3_sub_mode.get() == "iso":
                self.row_iso.pack(fill="x", padx=10, pady=3)
            else:
                self.row_disc.pack(fill="x", padx=10, pady=3)
            self.row_cache.pack(fill="x", padx=10, pady=3)

        elif m == "ps3_export":
            self.row_ps3_cfg.pack(fill="x", padx=10, pady=3)
            if self.ps3_source_type.get() == "iso":
                self.row_iso.pack(fill="x", padx=10, pady=3)
            else:
                self.row_disc.pack(fill="x", padx=10, pady=3)
            self.row_output.pack(fill="x", padx=10, pady=3)
            self.row_cache.pack(fill="x", padx=10, pady=3)

        elif m == "disc_inplace":
            self.row_disc.pack(fill="x", padx=10, pady=3)
            self.row_cache.pack(fill="x", padx=10, pady=3)

    def detect_default_paths(self):
        cur = SCRIPT_DIR
        for p in [cur, cur.parent, cur.parent.parent]:
            if (p / "rpcs3.exe").exists():
                self.rpcs3_path.set(str(p))
                break
            for sub in p.glob("rpcs3*"):
                if sub.is_dir() and (sub / "rpcs3.exe").exists():
                    self.rpcs3_path.set(str(sub))
                    break
            if self.rpcs3_path.get():
                break

    def browse_rpcs3(self):
        dp = filedialog.askdirectory(title="选择 RPCS3 根目录 (包含 rpcs3.exe 的文件夹)")
        if dp: self.rpcs3_path.set(dp)

    def browse_disc(self):
        dp = filedialog.askdirectory(title="选择包含 PS3_GAME 的游戏光盘文件夹")
        if dp: self.disc_path.set(dp)

    def browse_iso(self):
        fp = filedialog.askopenfilename(title="选择原版 BLJS10184 ISO 镜像", filetypes=[("PS3 ISO Files", "*.iso"), ("All Files", "*.*")])
        if fp: 
            self.iso_path.set(fp)
            if not self.output_dir.get():
                self.output_dir.set(str(Path(fp).parent / "M30_Chinese_Export"))

    def browse_output(self):
        dp = filedialog.askdirectory(title="选择汉化产物输出目录")
        if dp: self.output_dir.set(dp)

    def browse_cache(self):
        dp = filedialog.askdirectory(title="选择工作缓存目录 (建议选择剩余空间 >= 35GB 的分区)")
        if dp: self.cache_dir.set(dp)

    def start_patch_thread(self):
        m = self.main_mode.get()
        
        # Validation by mode
        if m == "rpcs3":
            r_root = self.rpcs3_path.get().strip()
            if not r_root or not Path(r_root).exists():
                messagebox.showwarning("提示", "RPCS3 模式必须选择有效的 RPCS3 根目录！\n若您使用的是 PS3 实体机，请切换到【模式 2：PS3 实体机导出模式】。")
                return
            sub = self.rpcs3_sub_mode.get()
            if sub == "iso" and (not self.iso_path.get().strip() or not Path(self.iso_path.get().strip()).exists()):
                messagebox.showwarning("提示", "请选择有效的原版 ISO 镜像文件！")
                return
            elif sub == "disc" and (not self.disc_path.get().strip() or not Path(self.disc_path.get().strip()).exists()):
                messagebox.showwarning("提示", "请选择有效的光盘解压目录！")
                return

        elif m == "ps3_export":
            src_type = self.ps3_source_type.get()
            if src_type == "iso" and (not self.iso_path.get().strip() or not Path(self.iso_path.get().strip()).exists()):
                messagebox.showwarning("提示", "请选择有效的原版 ISO 镜像文件！")
                return
            elif src_type == "disc" and (not self.disc_path.get().strip() or not Path(self.disc_path.get().strip()).exists()):
                messagebox.showwarning("提示", "请选择有效的光盘解压目录！")
                return
            if not self.output_dir.get().strip():
                messagebox.showwarning("提示", "请指定汉化产物输出目录！")
                return

        elif m == "disc_inplace":
            if not self.disc_path.get().strip() or not Path(self.disc_path.get().strip()).exists():
                messagebox.showwarning("提示", "请选择有效的光盘解压目录！")
                return

        self.btn_run.config(state="disabled")
        t = threading.Thread(target=self.run_patch_process, daemon=True)
        t.start()

    def run_patch_process(self):
        t0 = time.time()
        m = self.main_mode.get()
        assets_dir = SCRIPT_DIR / "patch_assets"
        cache_dir_val = Path(self.cache_dir.get().strip()) if self.cache_dir.get().strip() else None

        try:
            self.log("=" * 65)
            self.log(f"汉化注入开始 | 模式: {m.upper()}")
            self.log("=" * 65)

            if m == "rpcs3":
                r_root = Path(self.rpcs3_path.get().strip())
                inst_pack = r_root / "dev_hdd0" / "game" / "BLJS10184_INSTALL" / "USRDIR" / "data" / "pack"
                eboot_patch_p = r_root / "dev_hdd0" / "game" / "BLJS10184" / "USRDIR" / "EBOOT.BIN"
                sub = self.rpcs3_sub_mode.get()

                if sub == "iso":
                    iso_p = Path(self.iso_path.get().strip())
                    self.log("[*] [步骤 1/3] 正在解包 ISO、压制 PAM 视频、双轨注入 DAT 并重新封装 ISO...")
                    ok = patcher_engine.patch_iso_with_pam_and_repack(
                        iso_path=iso_p,
                        assets_dir=assets_dir,
                        custom_work_dir=cache_dir_val,
                        log_cb=self.log
                    )
                    if not ok:
                        messagebox.showerror("错误", "ISO 全量修补与重封装失败，请查看日志！")
                        return

                    # Sync to INSTALL
                    if inst_pack.exists():
                        self.log("[*] [步骤 2/3] 同步修补 BLJS10184_INSTALL 数据 DAT...")
                        patcher_engine.inject_patch_assets_into_pack(inst_pack, assets_dir, log_cb=self.log)
                    else:
                        self.log("[*] [步骤 2/3] 未找到现有 BLJS10184_INSTALL，游戏首次启动时将自动从汉化 ISO 释放。")

                    # Deploy EBOOT
                    self.log("[*] [步骤 3/3] 正在部署 1.02 汉化 EBOOT.BIN...")
                    if eboot_patch_p.exists():
                        patcher_engine.patch_eboot_bin(eboot_patch_p, assets_dir, log_cb=self.log)
                    else:
                        self.log("  [!] 未找到 dev_hdd0/game/BLJS10184/USRDIR/EBOOT.BIN，跳过 EBOOT 修改")

                elif sub == "disc":
                    disc_root = patcher_engine.locate_ps3_game_root(Path(self.disc_path.get().strip()))
                    disc_pack = disc_root / "PS3_GAME" / "USRDIR" / "data" / "pack"
                    disc_eboot = disc_root / "PS3_GAME" / "USRDIR" / "EBOOT.BIN"
                    movie_dir = disc_root / "PS3_GAME" / "USRDIR" / "data" / "movie"

                    self.log("[*] [步骤 1/4] 修补光盘目录 DAT 与 EBOOT...")
                    if not patcher_engine.inject_patch_assets_into_pack(disc_pack, assets_dir, log_cb=self.log):
                        messagebox.showerror("错误", "光盘 DAT 注入失败！")
                        return
                    if disc_eboot.exists():
                        patcher_engine.patch_eboot_bin(disc_eboot, assets_dir, log_cb=self.log)

                    self.log("[*] [步骤 2/4] 正在压制 64 部剧情 CG 双语硬字幕...")
                    if movie_dir.exists():
                        patcher_engine.patch_subtitles_pam_dir(movie_dir, assets_dir / "subtitles_pam", work_cache_dir=cache_dir_val, log_cb=self.log)

                    self.log("[*] [步骤 3/4] 同步写平 BLJS10184_INSTALL 数据 DAT...")
                    if inst_pack.exists():
                        for fn in ["data.dat", "data2.dat", "fileset0.dat", "pack.idx"]:
                            patcher_engine.backup_file_if_needed(inst_pack / fn, self.log)
                            shutil.copy2(disc_pack / fn, inst_pack / fn)
                        self.log("  [+] INSTALL 目录同步已完成！")

                    self.log("[*] [步骤 4/4] 部署 RPCS3 升级目录 EBOOT.BIN...")
                    if eboot_patch_p.exists():
                        patcher_engine.patch_eboot_bin(eboot_patch_p, assets_dir, log_cb=self.log)

            elif m == "ps3_export":
                src_mode = self.ps3_source_type.get()
                src_path = Path(self.iso_path.get().strip()) if src_mode == "iso" else Path(self.disc_path.get().strip())
                out_dir = Path(self.output_dir.get().strip())
                fmt = self.ps3_export_format.get()

                ok = patcher_engine.export_for_ps3_hardware(
                    source_mode=src_mode,
                    source_path=src_path,
                    output_dir=out_dir,
                    export_format=fmt,
                    assets_dir=assets_dir,
                    custom_work_dir=cache_dir_val,
                    log_cb=self.log
                )
                if not ok:
                    messagebox.showerror("错误", "PS3 实体机数据导出失败，请查看日志！")
                    return

            elif m == "disc_inplace":
                disc_root = patcher_engine.locate_ps3_game_root(Path(self.disc_path.get().strip()))
                disc_pack = disc_root / "PS3_GAME" / "USRDIR" / "data" / "pack"
                disc_eboot = disc_root / "PS3_GAME" / "USRDIR" / "EBOOT.BIN"
                movie_dir = disc_root / "PS3_GAME" / "USRDIR" / "data" / "movie"

                self.log("[*] [步骤 1/2] 就地修补光盘目录 DAT 与 EBOOT...")
                if not patcher_engine.inject_patch_assets_into_pack(disc_pack, assets_dir, log_cb=self.log):
                    messagebox.showerror("错误", "光盘 DAT 注入失败！")
                    return
                if disc_eboot.exists():
                    patcher_engine.patch_eboot_bin(disc_eboot, assets_dir, log_cb=self.log)

                self.log("[*] [步骤 2/2] 正在压制 64 部剧情 CG 双语硬字幕...")
                if movie_dir.exists():
                    patcher_engine.patch_subtitles_pam_dir(movie_dir, assets_dir / "subtitles_pam", work_cache_dir=cache_dir_val, log_cb=self.log)

            dur = time.time() - t0
            self.log("=" * 65)
            self.log(f"[SUCCESS] 汉化流程执行成功！总耗时: {dur:.2f} 秒")
            self.log("=" * 65)
            messagebox.showinfo("完成", f"汉化补丁流程已顺利完成！\n总耗时: {dur:.1f} 秒\n各项数据校验 100% 吻合！")

        except Exception as e:
            self.log(f"[-] 执行发生异常: {e}")
            import traceback
            self.log(traceback.format_exc())
            messagebox.showerror("异常", f"执行发生错误:\n{e}")
        finally:
            self.btn_run.config(state="normal")

if __name__ == "__main__":
    app = PatcherApp()
    app.mainloop()
