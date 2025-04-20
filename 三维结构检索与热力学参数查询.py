import tkinter as tk
from tkinter import messagebox
from Bio.PDB import PDBList, PDBParser
import nglview as nv
import pandas as pd
import os
import matplotlib
matplotlib.use('Agg')  # 避免与 tkinter 冲突的后端设置


# 设置文件路径
file_path = 'D://桌面//DNA'
df1 = pd.read_csv(os.path.join(file_path, 'DNA2025315.csv.csv'))
df2 = pd.read_csv(os.path.join(file_path, 'DNA2025316.csv.csv'))

# 明确指定列的数据类型
df1 = df1.astype({'Entry ID': 'str', 'Sequence': 'str'})
df2 = df2.astype({'Entry ID': 'str', 'Sequence': 'str'})

# 合并两个文件中的数据
df = pd.concat([df1, df2], ignore_index=True)

# 数据清洗：处理缺失值（这里简单填充空字符串，可根据实际情况调整）
df['Entry ID'] = df['Entry ID'].fillna('')
df['Sequence'] = df['Sequence'].fillna('')

# 初始化 PDB 下载器和解析器
pdbl = PDBList()
parser = PDBParser()


def preprocess_text(text):
    """对输入文本进行预处理，去除空格并转换为小写"""
    return text.strip().lower()


def search():
    search_text = entry.get()
    if not search_text:
        messagebox.showwarning("警告", "请输入 ID 或序列")
        return

    # 对输入文本进行预处理
    search_text = preprocess_text(search_text)

    # 对数据中的相关列进行预处理
    df['Entry ID_processed'] = df['Entry ID'].apply(preprocess_text)
    df['Sequence_processed'] = df['Sequence'].apply(preprocess_text)

    result_by_id = df[df['Entry ID_processed'] == search_text]
    result_by_sequence = df[df['Sequence_processed'] == search_text]

    if not result_by_id.empty:
        row = result_by_id.iloc[0]
        sequence = row['Sequence']
        delta_g = row['ΔG']
        delta_h = row['ΔH']
        delta_s = row['ΔS']
        tm = row['Tm (°C)'] if 'Tm (°C)' in row.index else 'N/A'
        pdb_id = row['Entry ID']

        result_text = f"ID: {search_text}\n序列: {sequence}\n热力学参数：ΔG: {delta_g}, ΔH: {delta_h}, ΔS: {delta_s}, Tm (°C): {tm}"

    elif not result_by_sequence.empty:
        row = result_by_sequence.iloc[0]
        entry_id = row['Entry ID']
        delta_g = row['ΔG']
        delta_h = row['ΔH']
        delta_s = row['ΔS']
        tm = row['Tm (°C)'] if 'Tm (°C)' in row.index else 'N/A'
        pdb_id = entry_id

        result_text = f"ID: {entry_id}\n序列: {search_text}\n热力学参数：ΔG: {delta_g}, ΔH: {delta_h}, ΔS: {delta_s}, Tm (°C): {tm}"
    else:
        result_text = "未找到匹配的记录"
        pdb_id = None

    result_textbox.config(state=tk.NORMAL)
    result_textbox.delete(1.0, tk.END)
    result_textbox.insert(tk.END, result_text)
    result_textbox.config(state=tk.DISABLED)

    return pdb_id


def display_structure():
    pdb_id = search()
    if pdb_id:
        try:
            print(f"开始下载 PDB 文件，ID 为 {pdb_id}")
            # 下载 PDB 文件
            pdb_file = pdbl.retrieve_pdb_file(pdb_id, pdir='.', file_format='pdb')
            print(f"PDB 文件下载完成，路径为 {pdb_file}")
            # 解析 PDB 文件
            structure = parser.get_structure(pdb_id, pdb_file)

            # 使用 nglview 展示结构
            view = nv.show_biopython(structure)
            view.add_ball_and_stick()

            # 创建一个新的 tkinter 窗口来展示结构
            new_window = tk.Tk()
            new_window.title(f"PDB ID {pdb_id} 三维结构")

            # 将 nglview 的视图嵌入到 tkinter 窗口中
            canvas = view._ngl_canvas
            canvas.master = new_window
            canvas.pack(fill=tk.BOTH, expand=True)

            new_window.mainloop()

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("错误", f"获取或展示 PDB ID 为 {pdb_id} 的结构时出错: {e}")
    else:
        messagebox.showinfo("信息", "没有可用于展示结构的 PDB ID")


root = tk.Tk()
root.title("DNA 检索工具")

label = tk.Label(root, text="输入 ID 或序列:")
label.pack(pady=10)

entry = tk.Entry(root, width=50)
entry.pack(pady=10)

search_button = tk.Button(root, text="检索信息", command=search)
search_button.pack(pady=10)

display_button = tk.Button(root, text="下载并展示三维结构", command=display_structure)
display_button.pack(pady=10)

result_textbox = tk.Text(root, width=80, height=10, state=tk.DISABLED)
result_textbox.pack(pady=10)

root.mainloop()