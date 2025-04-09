import tkinter as tk
from tkinter import messagebox
import os
import re


def get_dna_info(pdb_id):
    file_path = os.path.join('D:\\桌面\\DNA', f'{pdb_id}.pdb')
    if not os.path.exists(file_path):
        messagebox.showerror("文件未找到", f"在 D:\\桌面\\DNA 目录下未找到名为 {pdb_id}.pdb 的文件。请确认文件存在且文件名正确。")
        return None, None, None, None

    sequence = ""
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if line.startswith("SEQRES") and line.split()[2] == "DNA":
                    sequence += "".join(line.split()[4:])
    except UnicodeDecodeError:
        messagebox.showerror("编码错误", f"读取 {pdb_id}.pdb 文件时遇到编码问题。")
        return None, None, None, None

    # 计算序列长度
    try:
        length = len(sequence)
        # 简单的碱基配对计数（假设双链且互补配对）
        a_count = sequence.count('A')
        t_count = sequence.count('T')
        g_count = sequence.count('G')
        c_count = sequence.count('C')
        base_pairs = min(a_count, t_count) + min(g_count, c_count)
        # 简单假设的热力学参数（实际需更复杂计算）
        melting_temp = 4 * (g_count + c_count) + 2 * (a_count + t_count)
        delta_g = -0.5 * length  # 简单假设
        return length, base_pairs, melting_temp, delta_g
    except TypeError:
        messagebox.showerror("计算错误", "计算参数时出现数据类型错误。")
        return None, None, None, None


def search_pdb():
    pdb_id = entry.get().strip().upper()
    if not re.match(r"^[A - Z0 - 9]{4}$", pdb_id):
        messagebox.showerror("格式错误", "请输入有效的4位字母和数字组合的PDB ID。")
        return

    length, base_pairs, melting_temp, delta_g = get_dna_info(pdb_id)
    if length is not None:
        result_text = f"序列长度: {length}\n碱基配对数: {base_pairs}\n熔解温度 (假设值): {melting_temp} °C\nΔG (假设值): {delta_g} kcal/mol"
        messagebox.showinfo("结果", result_text)


# 创建主窗口
root = tk.Tk()
root.title("PDB DNA信息检索")

# 创建并放置输入框和按钮
tk.Label(root, text="输入PDB ID:").pack(pady=10)
entry = tk.Entry(root)
entry.pack(pady=10)
tk.Button(root, text="搜索", command=search_pdb).pack(pady=10)

# 运行主循环
root.mainloop()
