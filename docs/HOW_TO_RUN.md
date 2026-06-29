# 🧬 ST Agent 启动指南

## 环境信息

- **Python 环境**: `st_agent` (conda, Python 3.11)
- **项目目录**: `~/work0618/agent`
- **数据目录**: 项目根 `data/`（自动创建），可通过 `ST_AGENT_DATA_DIR` 环境变量自定义

---

## 一、安装依赖

```bash
# conda（推荐，leidenalg/h5py 在 Windows 上编译省心）
conda env create -f environment.yml
conda activate st_agent

# 或 pip
pip install -r requirements.txt
```

## 二、配置 API Key（首次必须）

```bash
cp .env.example .env
# 编辑 .env，至少填 DEEPSEEK_API_KEY
```

`.env` 内容：
```
DEEPSEEK_API_KEY=sk-xxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

## 三、下载 GSE278603 数据集（可选）

```bash
mkdir -p data && cd data
curl -O "ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE278nnn/GSE278603/suppl/GSE278603_RAW.tar"
tar -xvf GSE278603_RAW.tar
ls -lh *.h5ad
```

推荐先用最小的测试：`GSM9046247_Embryo_E8.0_stereo_rep1.h5ad` (37MB)

## 四、启动 App

```bash
cd ~/work0618/agent
streamlit run app.py
```

浏览器打开 `http://localhost:8501`。**`Email:` 提示直接按回车跳过**。

## 五、使用 App

1. **侧边栏顶部** — 🇨🇳 中文 / 🇬🇧 English
2. **侧边栏 "数据"** — 上传 `.h5ad` 或粘贴文件路径
3. **侧边栏 "参数"** — 调整 HVG 数、Leiden 分辨率、PC 数
4. **底部聊天框** — 输入自然语言指令

## 六、常用指令

| 指令 | 说明 |
|------|------|
| `加载数据，跑完整基础分析流程` | 标准流水线 |
| `显示 Sox2 和 T 的空间表达` | 单基因空间分布 |
| `用 resolution=0.8 聚类` | 调整参数 |
| `找 marker 基因并做 GO 富集` | 扩展分析 |
| `比较 E7.5 和 E8.0 的差异` | 跨阶段对比 |
| `生成HTML分析报告` | 报告下载 |

## 七、常见问题

| 问题 | 解决 |
|------|------|
| `streamlit: command not found` | `conda activate st_agent` 或 `pip install streamlit` |
| `ModuleNotFoundError: No module named 'agent'` | 确保在项目根目录下运行 |
| h5py 写文件报错 | WSL 下上传的文件自动存到系统临时目录 |
| 图片显示乱码 | 点下载按钮下载 PNG/HTML 查看 |
| 细胞通讯无结果 | 需要先跑 `run_preprocess` |
| 富集/知识/文献无结果 | 需要外网：Enrichr / MyGene / PubMed API |
| DeepSeek 规划失败 | 检查 `.env` 中 API key |

## 八、自定义数据目录

```bash
export ST_AGENT_DATA_DIR=/your/custom/path
streamlit run app.py
```

## 快速记忆卡

```bash
# 启动
cd ~/work0618/agent && streamlit run app.py
# 安装
conda env create -f environment.yml
```
