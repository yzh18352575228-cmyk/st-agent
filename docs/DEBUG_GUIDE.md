# ST Agent 调试指南

## 零、最速诊断（30 秒定位问题）

```bash
cd ~/work0618/agent

# 1. 代码能不能跑？
python -c "from agent.graph import build_graph; build_graph(); print('核心 OK')"

# 2. 所有工具能不能导入？
python -c "from agent.tools import TOOL_REGISTRY; print(f'{len(TOOL_REGISTRY)} 个工具可用')"
```

## 一、按症状分类排查

### 症状 A：Streamlit 启动失败

```bash
# 确认在项目根目录下执行
cd ~/work0618/agent
streamlit run app.py

# 如果报 ModuleNotFoundError: No module named 'streamlit'
pip install streamlit
```

### 症状 B：Agent 回答"没有看到数据"但明明加载了

检查文件路径是否是 Windows 原生路径（WSL 用户），确认 `tool_load_data` 返回了确认信息。

### 症状 C：图表白底白字/看不清

Streamlit 设置 → 关闭暗色主题（Settings → Theme → Light）。

### 症状 D：某些分析步骤静默失败

| 工具 | 常见失败原因 | 解决 |
|------|-------------|------|
| `run_cell_communication` | 数据未归一化/没有 LR 基因 | 先跑 `run_preprocess` |
| `run_neighborhood_analysis` | spatial key 不匹配 | 检查 `adata.obsm.keys()` |
| `run_svg_analysis` | 空间邻域图未建立 | 超大数据可能超时 |
| `run_enrichment_analysis` | 无网络/Enrichr API 挂了 | 检查外网连接 |
| `cross_stage_comparison` | 只有 1 个文件/slice | 确保 `merge_samples` 先执行 |

### 症状 E：DeepSeek API 不响应

检查 API key 配置、网络连通性、`.env` 文件是否存在。

### 症状 F：h5py 写文件报错

UNC/WSL 路径问题。WSL 用户上传的 .h5ad 会自动存到系统临时目录。非 WSL 用户直接用项目 `data/` 目录即可。

## 二、环境相关调试

### 确认 conda 环境完整

```bash
conda run -n st_agent pip list | grep -E "scanpy|squidpy|langgraph|streamlit|plotly"
```

### 常见错误速查表

| 错误信息 | 修复 |
|---------|------|
| `No module named 'agent'` | `cd ~/work0618/agent` |
| `ValueError: X_pca does not have enough PCs` | 自动检测 `X_pca.shape[1]` 已修复 |
| `ModuleNotFoundError: No module named 'dotenv'` | pip install python-dotenv |
| `OOM / MemoryError` | 用更小的文件（E8.0 rep1=37MB） |

## 三、终极恢复流程

```bash
# 1. 清状态
rm -rf data/figures/ data/reports/ data/conversation_log.md

# 2. 验证代码
cd ~/work0618/agent
python tests/e2e_validate.py --skip-llm

# 3. 重启 Streamlit
streamlit run app.py
```
