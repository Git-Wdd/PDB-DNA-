import time
import os
import re
import requests
import pandas as pd
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 配置信息
UNAFOLD_URL = "https://www.unafold.org/Dinamelt/applications/two-state-melting-folding.php"
CSV_FILE_PATH =r'D:\DNA\DNA2025315.csv.csv'
OUTPUT_DIR = "structure_pdfs"

# 初始化环境
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 浏览器配置
options = webdriver.ChromeOptions()
options.add_argument("--headless")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
driver.set_page_load_timeout(180)

# 读取数据并预处理
df = pd.read_csv(CSV_FILE_PATH, encoding="utf-8")
df["ΔG"] = df["ΔH"] = df["ΔS"] = df["Tm (°C)"] = ""

# 预处理步骤：生成有效Entry ID、总次数和顺序索引
effective_entries = []
current_entry = None
entry_counts = defaultdict(int)
entry_order = defaultdict(int)

# 第一次遍历：确定有效Entry ID和总次数
for idx, row in df.iterrows():
    raw_entry = row["Entry ID"]
    entry = str(raw_entry).strip() if pd.notna(raw_entry) and str(raw_entry).strip() != "nan" else None
    if entry:
        current_entry = entry
    effective_entries.append(current_entry)
    if current_entry:
        entry_counts[current_entry] += 1

# 第二次遍历：确定顺序索引
order_indices = []
entry_tracker = defaultdict(int)
for entry in effective_entries:
    if entry:
        order_indices.append(entry_tracker[entry])
        entry_tracker[entry] += 1
    else:
        order_indices.append(0)

# 将预处理结果添加到DataFrame
df["effective_entry"] = effective_entries
df["total_count"] = [entry_counts.get(entry, 0) if entry else 0 for entry in effective_entries]
df["order_index"] = order_indices

# 处理逻辑
def generate_filename(row):
    """生成最终文件名"""
    entry = row["effective_entry"]
    total = row["total_count"]
    idx = row["order_index"]
    
    if not entry:
        return f"row{row.name + 1}_X"
    
    if total <= 1:
        return entry
    else:
        return f"{entry}_{chr(65 + idx)}"


for idx, row in df.iterrows():
    current_line = idx + 1
    sequence = str(row["Sequence"]).strip()
    

    
    # ========== 2. 生成文件名 ==========
    filename_tag = generate_filename(row)
    pdf_path = os.path.join(OUTPUT_DIR, f"{filename_tag}_structure.pdf")
    
    # ========== 3. 打印处理信息 ==========
    print(f"\n🔍 正在处理 {filename_tag}, 序列: {sequence[:15]}...")
    
    # ========== 4. 网站交互流程 ==========
    try:
        # 访问网站并输入序列
        driver.get(UNAFOLD_URL)
        input_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="seq"]'))
        )
        input_box.clear()
        input_box.send_keys(sequence)
        
        # 选择能量规则
        driver.find_element(By.XPATH, '/html/body/main/div[2]/form/p[4]/select[1]').send_keys("DNA")
        
        # 提交表单
        driver.find_element(By.XPATH, '/html/body/main/div[2]/form/p[6]/input[1]').click()
        time.sleep(5)
        
        # ========== 5. 提取热力学参数 ==========
        result_row = driver.find_element(By.XPATH, "/html/body/main/div[2]/div/table/tbody/tr")
        raw_text = result_row.text.replace("=", "").replace("°C", "")
        parts = raw_text.split()
        
        params = {
            "ΔG": parts[2] if len(parts) > 2 else "N/A",
            "ΔH": parts[4] if len(parts) > 4 else "N/A",
            "ΔS": parts[6] if len(parts) > 6 else "N/A",
            "Tm (°C)": parts[8] if len(parts) > 8 else "N/A"
        }
        print(f"✅ 提取参数: ΔG={params['ΔG']}, ΔH={params['ΔH']}, ΔS={params['ΔS']}, Tm={params['Tm (°C)']}")
        
    except Exception as e:
        print(f"❌ 处理异常: {str(e)}")
        params = {"ΔG": "ERROR", "ΔH": "ERROR", "ΔS": "ERROR", "Tm (°C)": "ERROR"}
    
    # ========== 7. 更新数据 ==========
    df.at[idx, "ΔG"] = params["ΔG"]
    df.at[idx, "ΔH"] = params["ΔH"]
    df.at[idx, "ΔS"] = params["ΔS"]
    df.at[idx, "Tm (°C)"] = params["Tm (°C)"]
    df.to_csv(CSV_FILE_PATH, index=False)
    print(f"🔄 已更新 {filename_tag} 的热力学参数到CSV文件")

# 清理资源
driver.quit()
print("\n✅ 处理完成！")