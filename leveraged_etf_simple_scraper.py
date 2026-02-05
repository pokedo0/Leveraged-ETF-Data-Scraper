"""
杠杆ETF数据爬取脚本 - 简单版（无需浏览器）
直接从 leveragedposition.com 页面HTML中提取JSON数据
"""

import requests
import json
import re
import pandas as pd


def fetch_etf_data():
    """从网站获取所有ETF数据"""
    print("=" * 70)
    print("杠杆ETF数据爬取工具 - 简单版")
    print("=" * 70)
    
    url = "https://leveragedposition.com/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    print(f"\n正在获取: {url}")
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    
    html_content = response.text
    print(f"页面大小: {len(html_content):,} 字节")
    
    all_etfs = []
    
    # 方法1: 查找 "initialData":[ 后面的JSON数组
    # Next.js会将数据编码在script标签中
    
    # 查找所有 script 标签内容
    script_pattern = r'<script[^>]*>([\s\S]*?)</script>'
    scripts = re.findall(script_pattern, html_content)
    
    for script in scripts:
        if '"initialData":[{' in script or '"ticker":' in script:
            # 查找 initialData 数组
            init_match = re.search(r'"initialData":\s*(\[\{.*?\}\])', script, re.DOTALL)
            if init_match:
                try:
                    data = json.loads(init_match.group(1))
                    if isinstance(data, list) and len(data) > 0:
                        print(f"✓ 方法1: 找到 {len(data)} 条数据")
                        all_etfs = data
                        break
                except:
                    pass
    
    # 方法2: 查找 self.__next_f.push 中的编码数据
    if not all_etfs:
        print("尝试方法2: 解析 Next.js 编码数据...")
        
        # 查找所有 push 调用
        push_pattern = r'self\.__next_f\.push\(\[1,\s*"(.+?)"\s*\]\)'
        pushes = re.findall(push_pattern, html_content)
        
        combined_data = ""
        for push_content in pushes:
            # 解码转义字符
            try:
                decoded = push_content.encode('utf-8').decode('unicode_escape')
                combined_data += decoded
            except:
                combined_data += push_content
        
        # 在解码后的数据中查找 initialData
        if '"initialData":' in combined_data:
            # 查找 initialData 后面的数组
            start = combined_data.find('"initialData":[')
            if start != -1:
                start = combined_data.find('[', start)
                # 找到匹配的结束括号
                bracket_count = 0
                end = start
                for i, char in enumerate(combined_data[start:], start):
                    if char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            end = i + 1
                            break
                
                json_str = combined_data[start:end]
                try:
                    data = json.loads(json_str)
                    if isinstance(data, list) and len(data) > 0:
                        print(f"✓ 方法2: 找到 {len(data)} 条数据")
                        all_etfs = data
                except json.JSONDecodeError as e:
                    print(f"JSON解析错误: {e}")
    
    # 方法3: 直接查找包含ticker的JSON对象
    if not all_etfs:
        print("尝试方法3: 直接查找ETF数据...")
        
        # 查找所有 {"ticker": 开头的JSON对象
        ticker_pattern = r'\{"ticker":"([A-Z0-9]+)"[^}]*"name":"([^"]+)"[^}]*"underlying_asset":("[^"]*"|null)[^}]*"leverage":("[^"]*"|null)[^}]*"direction":("[^"]*"|null)[^}]*\}'
        
        matches = re.findall(ticker_pattern, html_content)
        if matches:
            print(f"  找到 {len(matches)} 个匹配")
    
    # 方法4: 查找完整的ETF对象数组
    if not all_etfs:
        print("尝试方法4: 搜索完整JSON数组...")
        
        # 用更宽松的模式查找
        # 查找: [{"ticker":"AALG",.....},{"ticker":"AAPB",...}]
        array_start = html_content.find('[{"ticker":"')
        if array_start != -1:
            # 找到数组结束
            bracket_count = 0
            end_pos = array_start
            in_string = False
            escape_next = False
            
            for i, char in enumerate(html_content[array_start:], array_start):
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\':
                    escape_next = True
                    continue
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if not in_string:
                    if char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            end_pos = i + 1
                            break
            
            if end_pos > array_start:
                json_str = html_content[array_start:end_pos]
                try:
                    data = json.loads(json_str)
                    if isinstance(data, list) and len(data) > 0:
                        print(f"✓ 方法4: 找到 {len(data)} 条数据")
                        all_etfs = data
                except json.JSONDecodeError as e:
                    print(f"  JSON解析错误位置附近: {json_str[:200]}...")
    
    return all_etfs


def extract_key_info(etf_data):
    """提取所有信息，核心字段排在前面"""
    key_info = []
    
    # 核心字段（排在最前面）
    priority_fields = [
        'ticker', 'name', 'underlying_asset', 'underlying_ticker', 
        'leverage', 'direction'
    ]
    
    for etf in etf_data:
        if not etf.get('ticker'):
            continue
        
        # 使用有序字典确保字段顺序
        info = {}
        
        # 先添加核心字段
        for field in priority_fields:
            info[field] = etf.get(field, '')
        
        # 再添加所有其他字段
        for key, value in etf.items():
            if key not in priority_fields:
                info[key] = value if value is not None else ''
        
        key_info.append(info)
    
    return key_info


def display_and_save_data(etfs):
    """显示并保存数据"""
    if not etfs:
        print("\n✗ 未获取到数据")
        return None
    
    print("\n" + "=" * 70)
    print(f"成功提取 {len(etfs)} 只杠杆ETF信息")
    print("=" * 70)
    
    # 提取关键信息
    key_info = extract_key_info(etfs)
    df = pd.DataFrame(key_info)
    
    # 显示关键列
    print("\n【标的名称和杠杆倍率信息】（前50条）")
    print("-" * 70)
    
    key_columns = ['ticker', 'name', 'underlying_asset', 'leverage', 'direction']
    available_columns = [col for col in key_columns if col in df.columns]
    
    if available_columns:
        display_df = df[available_columns].copy()
        # 截断过长的名称
        if 'name' in display_df.columns:
            display_df['name'] = display_df['name'].apply(
                lambda x: (str(x)[:35] + '...') if pd.notna(x) and len(str(x)) > 35 else x
            )
        if 'underlying_asset' in display_df.columns:
            display_df['underlying_asset'] = display_df['underlying_asset'].apply(
                lambda x: (str(x)[:25] + '...') if pd.notna(x) and len(str(x)) > 25 else x
            )
        
        print(display_df.head(50).to_string(index=False))
        
        if len(df) > 50:
            print(f"\n... 还有 {len(df) - 50} 条数据")
    
    # 保存完整数据到CSV
    output_file = 'leveraged_etf_data.csv'
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n✓ 完整数据已保存到: {output_file}")
    
    # 保存JSON
    json_file = 'leveraged_etf_data.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(key_info, f, ensure_ascii=False, indent=2)
    print(f"✓ JSON数据已保存到: {json_file}")
    
    # 只保存标的名称和杠杆倍率的简化版本
    simple_file = 'leveraged_etf_simple.csv'
    simple_df = df[['ticker', 'name', 'underlying_asset', 'underlying_ticker', 'leverage', 'direction']].copy()
    simple_df = simple_df.dropna(subset=['ticker'])
    simple_df.to_csv(simple_file, index=False, encoding='utf-8-sig')
    print(f"✓ 简化版数据已保存到: {simple_file}")
    
    # 统计
    print("\n【统计信息】")
    print("-" * 70)
    print(f"总数: {len(df)} 只ETF")
    
    if 'leverage' in df.columns:
        leverage_counts = df['leverage'].value_counts().head(10)
        print("\n杠杆分布 (前10):")
        for lev, count in leverage_counts.items():
            print(f"  {lev}: {count} 只")
    
    if 'direction' in df.columns:
        direction_counts = df['direction'].value_counts()
        print("\n方向分布:")
        for dir_name, count in direction_counts.items():
            if pd.notna(dir_name):
                print(f"  {dir_name}: {count} 只")
    
    if 'asset_class' in df.columns:
        asset_counts = df['asset_class'].value_counts()
        print("\n资产类型分布:")
        for asset, count in asset_counts.items():
            if pd.notna(asset):
                print(f"  {asset}: {count} 只")
    
    if 'fund_family' in df.columns:
        family_counts = df['fund_family'].value_counts().head(10)
        print("\n基金公司分布 (前10):")
        for family, count in family_counts.items():
            if pd.notna(family):
                print(f"  {family}: {count} 只")
    
    return df


def main():
    # 获取数据
    etfs = fetch_etf_data()
    
    if etfs:
        # 显示并保存
        df = display_and_save_data(etfs)
        return df
    else:
        print("\n✗ 未能获取数据")
        return None


if __name__ == "__main__":
    main()
