# Leveraged ETF Data Scraper

自动从 [leveragedposition.com](https://leveragedposition.com/) 抓取杠杆ETF数据。

## 功能

- 📊 自动提取 **755+ 只杠杆ETF** 的完整信息
- 🕐 每月第一天自动运行（也可手动触发）
- 📁 生成 CSV 和 JSON 格式数据
- 🚀 通过 GitHub Releases 提供下载

## 数据字段

### 核心字段（排在最前）

| 字段                | 说明                                            |
| ------------------- | ----------------------------------------------- |
| `ticker`            | ETF代码                                         |
| `name`              | ETF名称                                         |
| `underlying_asset`  | 标的资产名称                                    |
| `underlying_ticker` | 标的资产代码                                    |
| `leverage`          | 杠杆倍率 (1x, 1.2x, 1.5x, 2x, 3x, 4x, variable) |
| `direction`         | 方向 (long/short)                               |

### 其他字段

- `price` - 价格
- `aum` - 资产管理规模
- `avg_volume` - 平均成交量
- `expense_ratio` - 费用率
- `fund_family` - 基金公司
- `asset_class` - 资产类别
- `inception_date` - 成立日期
- `ytd_returns` - 年初至今收益
- 等等...

## 使用方法

### 本地运行

```bash
pip install -r requirements.txt
python leveraged_etf_simple_scraper.py
```

### GitHub Action

- **自动运行**: 每月第一天 UTC 00:00（北京时间 08:00）
- **手动触发**: Actions → Scrape Leveraged ETF Data → Run workflow

## 下载数据

前往 [Releases](../../releases) 页面下载最新数据。

## 输出文件

| 文件                       | 说明                 |
| -------------------------- | -------------------- |
| `leveraged_etf_data.csv`   | 完整数据（所有字段） |
| `leveraged_etf_data.json`  | JSON格式完整数据     |
| `leveraged_etf_simple.csv` | 简化版（核心字段）   |

## License

MIT
