# -*- coding: utf-8 -*-
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
        self.title("超时空要塞 30：联系银河的歌声 - 汉化补丁器 v1.4")
        self.geometry("740x600")
        self.minsize(680, 520)
        
        self.target_mode = tk.StringVar(value="iso")
        self.rpcs3_path = tk.StringVar(value="")
        self.iso_path = tk.StringVar(value="")
        self.disc_path = tk.StringVar(value="")
        
        self.create_widgets()
        self.detect_default_paths()

    def create_widgets(self):
        pad = {"padx": 10, "pady": 5}
        
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", **pad)
        lbl_title = ttk.Label(header_frame, text="超时空要塞 30 中文汉化补丁器", font=("Microsoft YaHei", 14, "bold"))
        lbl_title.pack(anchor="w")
        lbl_sub = ttk.Label(header_frame, text="成对修补光盘端与硬盘端 DAT 并同步部署汉化 EBOOT，内置全量 SHA-256 校验", font=("Microsoft YaHei", 9))
        lbl_sub.pack(anchor="w")

        # Mode Selection
        mode_frame = ttk.LabelFrame(self, text="【选择修补模式】")
        mode_frame.pack(fill="x", **pad)
        
        r1 = ttk.Radiobutton(mode_frame, text="模式 1：ISO 镜像模式 (修补 PAM 视频与 DAT 并重新封装 ISO)", 
                             variable=self.target_mode, value="iso", command=self.on_mode_changed)
        r1.pack(anchor="w", padx=10, pady=4)
        lbl_desc1 = ttk.Label(mode_frame, text="  解包 ISO，压制 64 部 PAM，双轨注入DAT并重新生成汉化 ISO，同步更新 INSTALL 与 EBOOT。", font=("Microsoft YaHei", 8), foreground="gray")
        lbl_desc1.pack(anchor="w", padx=10, pady=(0, 4))
        
        r2 = ttk.Radiobutton(mode_frame, text="模式 2：解压光盘目录模式 (修补 光盘文件夹 + 压制 PAM + INSTALL + EBOOT)", 
                             variable=self.target_mode, value="disc", command=self.on_mode_changed)
        r2.pack(anchor="w", padx=10, pady=4)
        lbl_desc2 = ttk.Label(mode_frame, text="  修补 PS3_GAME 目录中的 DAT 与 EBOOT，压制 64 部 PAM 视频，同步更新 INSTALL 与 EBOOT。", font=("Microsoft YaHei", 8), foreground="gray")
        lbl_desc2.pack(anchor="w", padx=10, pady=(0, 4))

        # Path Inputs
        path_frame = ttk.LabelFrame(self, text="【指定路径】")
        path_frame.pack(fill="x", **pad)
        
        # Row: RPCS3 Root
        row_rpcs3 = ttk.Frame(path_frame)
        row_rpcs3.pack(fill="x", padx=10, pady=4)
        lbl_rpcs3 = ttk.Label(row_rpcs3, text="RPCS3 根目录:", width=14)
        lbl_rpcs3.pack(side="left")
        self.ent_rpcs3 = ttk.Entry(row_rpcs3, textvariable=self.rpcs3_path)
        self.ent_rpcs3.pack(side="left", fill="x", expand=True, padx=6)
        btn_browse_rpcs3 = ttk.Button(row_rpcs3, text="浏览...", command=self.browse_rpcs3)
        btn_browse_rpcs3.pack(side="right")

        # Row: ISO File (Mode 1)
        self.row_iso = ttk.Frame(path_frame)
        lbl_iso = ttk.Label(self.row_iso, text="原版 ISO 文件:", width=14)
        lbl_iso.pack(side="left")
        self.ent_iso = ttk.Entry(self.row_iso, textvariable=self.iso_path)
        self.ent_iso.pack(side="left", fill="x", expand=True, padx=6)
        btn_browse_iso = ttk.Button(self.row_iso, text="浏览...", command=self.browse_iso)
        btn_browse_iso.pack(side="right")

        # Row: Disc Folder (Mode 2)
        self.row_disc = ttk.Frame(path_frame)
        lbl_disc = ttk.Label(self.row_disc, text="光盘解压目录:", width=14)
        lbl_disc.pack(side="left")
        self.ent_disc = ttk.Entry(self.row_disc, textvariable=self.disc_path)
        self.ent_disc.pack(side="left", fill="x", expand=True, padx=6)
        btn_browse_disc = ttk.Button(self.row_disc, text="浏览...", command=self.browse_disc)
        btn_browse_disc.pack(side="right")

        # Action Button
        act_frame = ttk.Frame(self)
        act_frame.pack(fill="x", **pad)
        self.btn_run = ttk.Button(act_frame, text="开始执行汉化注入", command=self.start_patch_thread)
        self.btn_run.pack(side="left", fill="x", expand=True, ipady=4)
        
        # Log Output Area
        log_frame = ttk.LabelFrame(self, text="【执行日志】")
        log_frame.pack(fill="both", expand=True, **pad)
        self.log_txt = scrolledtext.ScrolledText(log_frame, font=("Consolas", 9), wrap="word")
        self.log_txt.pack(fill="both", expand=True, padx=6, pady=6)

        self.on_mode_changed()

    def log(self, text_line):
        self.log_txt.insert("end", text_line + "\n")
        self.log_txt.see("end")

    def on_mode_changed(self):
        m = self.target_mode.get()
        if m == "iso":
            self.row_iso.pack(fill="x", padx=10, pady=4)
            self.row_disc.pack_forget()
        elif m == "disc":
            self.row_disc.pack(fill="x", padx=10, pady=4)
            self.row_iso.pack_forget()

    def detect_default_paths(self):
        # Scan relative/adjacent directories without hardcoding personal absolute paths
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
        dp = filedialog.askdirectory(title="选择 RPCS3 根目录 (包含 rpcs3.exe 的目录)")
        if dp: self.rpcs3_path.set(dp)

    def browse_disc(self):
        dp = filedialog.askdirectory(title="选择光盘解压目录 (包含 PS3_GAME 的目录)")
        if dp: self.disc_path.set(dp)

    def browse_iso(self):
        fp = filedialog.askopenfilename(title="选择原版 BLJS10184 ISO 镜像", filetypes=[("PS3 ISO Files", "*.iso"), ("All Files", "*.*")])
        if fp: self.iso_path.set(fp)

    def start_patch_thread(self):
        m = self.target_mode.get()
        r_root = self.rpcs3_path.get().strip()
        if not r_root or not Path(r_root).exists():
            messagebox.showwarning("提示", "请先选择有效的 RPCS3 根目录！")
            return
        
        if m == "iso" and (not self.iso_path.get().strip() or not Path(self.iso_path.get().strip()).exists()):
            messagebox.showwarning("提示", "请先选择有效的原版 ISO 文件！")
            return
        elif m == "disc" and (not self.disc_path.get().strip() or not Path(self.disc_path.get().strip()).exists()):
            messagebox.showwarning("提示", "请先选择有效的光盘解压目录！")
            return
        
        self.btn_run.config(state="disabled")
        t = threading.Thread(target=self.run_patch_process, daemon=True)
        t.start()

    def run_patch_process(self):
        t0 = time.time()
        m = self.target_mode.get()
        assets_dir = SCRIPT_DIR / "patch_assets"
        r_root = Path(self.rpcs3_path.get().strip())
        inst_pack = r_root / "dev_hdd0" / "game" / "BLJS10184_INSTALL" / "USRDIR" / "data" / "pack"
        eboot_patch_p = r_root / "dev_hdd0" / "game" / "BLJS10184" / "USRDIR" / "EBOOT.BIN"

        try:
            self.log("=" * 65)
            self.log("开始执行汉化注入 (模式: " + ("全量 ISO 修补 + 重封装" if m == "iso" else "光盘目录全量修补") + ")")
            self.log("=" * 65)

            if m == "iso":
                iso_p = Path(self.iso_path.get().strip())
                
                # 1. Full unpack, patch PAM + pack, and repack ISO
                self.log("[*] [步骤 1/3] 正在解包 ISO、压制 PAM 视频、双轨注入 DAT 并重新封装 ISO...")
                ok = patcher_engine.patch_iso_with_pam_and_repack(iso_p, assets_dir, log_cb=self.log)
                if not ok:
                    messagebox.showerror("错误", "ISO 全量修补与重封装失败，请查看日志！")
                    return

                # 2. Patch INSTALL pack
                if inst_pack.exists():
                    self.log("[*] [步骤 2/3] 正在同步修补 BLJS10184_INSTALL 数据 DAT ...")
                    ok = patcher_engine.inject_patch_assets_into_pack(inst_pack, assets_dir, log_cb=self.log)
                    if not ok:
                        messagebox.showerror("错误", "INSTALL  DAT 注入失败，请查看日志！")
                        return
                else:
                    self.log("[*] [步骤 2/3] 未找到现有 BLJS10184_INSTALL，游戏首次启动时将自动从汉化 ISO 释放。")

                # 3. Deploy EBOOT
                self.log("[*] [步骤 3/3] 正在部署汉化 EBOOT.BIN...")
                if eboot_patch_p.exists():
                    patcher_engine.patch_eboot_bin(eboot_patch_p, assets_dir, log_cb=self.log)
                else:
                    self.log("  [!] 未找到 dev_hdd0/game/BLJS10184/USRDIR/EBOOT.BIN，跳过 EBOOT 修改")

            elif m == "disc":
                disc_root = Path(self.disc_path.get().strip())
                disc_pack = disc_root / "PS3_GAME" / "USRDIR" / "data" / "pack" if (disc_root / "PS3_GAME").exists() else disc_root / "USRDIR" / "data" / "pack"
                disc_eboot = disc_root / "PS3_GAME" / "USRDIR" / "EBOOT.BIN" if (disc_root / "PS3_GAME").exists() else disc_root / "USRDIR" / "EBOOT.BIN"
                movie_dir = disc_pack.parent / "movie"
                
                # 1. Patch disc pack & eboot
                self.log("[*] [步骤 1/4] 正在修补光盘解压目录 DAT 与 EBOOT...")
                ok = patcher_engine.inject_patch_assets_into_pack(disc_pack, assets_dir, log_cb=self.log)
                if not ok:
                    messagebox.showerror("错误", "光盘 DAT 注入失败，请查看日志！")
                    return
                if disc_eboot.exists():
                    patcher_engine.patch_eboot_bin(disc_eboot, assets_dir, log_cb=self.log)

                # 2. Mandatory PAM burning for disc mode
                self.log("[*] [步骤 2/4] 正在处理 64 部剧情 CG 双语硬字幕...")
                if movie_dir.exists():
                    patcher_engine.patch_subtitles_pam_dir(movie_dir, assets_dir / "subtitles_pam", log_cb=self.log)

                # 3. Sync to INSTALL pack
                self.log("[*] [步骤 3/4] 正在同步写平 BLJS10184_INSTALL 数据 DAT ...")
                if inst_pack.exists():
                    for fn in ["data.dat", "data2.dat", "fileset0.dat", "pack.idx"]:
                        patcher_engine.backup_file_if_needed(inst_pack / fn, self.log)
                        shutil.copy2(disc_pack / fn, inst_pack / fn)
                    self.log("  [+] INSTALL 目录同步已完成！")
                else:
                    self.log("  [!] 未检测到 BLJS10184_INSTALL 目录，跳过同步")

                # 4. Sync to RPCS3 update eboot
                self.log("[*] [步骤 4/4] 正在部署 RPCS3 升级目录 EBOOT.BIN...")
                if eboot_patch_p.exists():
                    patcher_engine.patch_eboot_bin(eboot_patch_p, assets_dir, log_cb=self.log)
                else:
                    self.log("  [!] 未找到 dev_hdd0/game/BLJS10184/USRDIR/EBOOT.BIN，跳过 EBOOT 修改")

            dur = time.time() - t0
            self.log("=" * 65)
            self.log("汉化补丁注入成功！总耗时: " + f"{dur:.2f}" + " 秒")
            self.log("=" * 65)
            messagebox.showinfo("完成", "汉化补丁注入完成！总耗时 " + f"{dur:.1f}" + " 秒。\n已完成两端一致性校验！")

        except Exception as e:
            self.log("[-] 执行发生异常: " + str(e))
            messagebox.showerror("异常", "执行发生错误:\n" + str(e))
        finally:
            self.btn_run.config(state="normal")

if __name__ == "__main__":
    app = PatcherApp()
    app.mainloop()
    app = PatcherApp()
    app.mainloop()
