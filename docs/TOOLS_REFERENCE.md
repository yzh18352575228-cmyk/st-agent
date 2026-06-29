# ST Agent 工具参考手册

22 个可调用工具，分为 6 个类别。所有工具可通过自然语言在 Streamlit 聊天中调用。

---

## 一、数据工具 (4)

### load_data
加载单个 .h5ad 文件到工作内存。
参数：file_path（路径）| 返回：细胞数 × 基因数 + 空间坐标信息

### load_multiple
通过通配符一次加载多个 .h5ad 文件，自动识别发育阶段。
参数：glob_pattern（通配符路径）| 返回：每文件概要表 + 总文件数/细胞数

### get_overview
查看当前已加载数据的基本信息。
返回：细胞数、基因数、obs/var/obsm 列、空间坐标状态

### get_cell_stats
从真实数据读取细胞级别的指标（不编造任何数字）。
参数：obs_column（默认 pct_counts_mt）、n_cells（默认 20）| 前提：需要先跑 run_qc

---

## 二、核心分析流水线 (4)

### run_qc
质量控制：过滤低质量细胞和基因，生成 QC 图表。
参数：min_genes(200), min_cells(3), max_mito_pct(20.0) | 返回：3 张图（小提琴/散点/直方图）

### run_preprocess
数据预处理：归一化、log 变换、高变基因筛选、PCA 降维。
参数：n_hvg(2000), n_pcs(30) | 返回：2 张图（HVG 散点/PCA 肘部图）| 前提：需要先跑 run_qc

### run_clustering
UMAP 降维 + Leiden 聚类。
参数：resolution(1.0), n_neighbors(15) | 返回：2 张图（UMAP/簇大小柱状图）| 前提：需要先跑 run_preprocess

### run_marker_analysis
差异表达分析：找出每个 cluster 的标记基因。
参数：cluster_key("leiden"), n_genes(10), method("wilcoxon") | 返回：dotplot + top 基因排名表 | 前提：需要先跑 run_clustering

---

## 三、空间可视化 (2)

### plot_spatial_clusters
在组织空间坐标上按 cluster 着色展示细胞分布。参数：cluster_key("leiden") | 前提：需要空间坐标 + cluster

### plot_spatial_gene
在空间坐标上按指定基因表达量着色。参数：gene_name（基因名）| 前提：需要空间坐标

---

## 四、空间高级分析 (4)

### run_neighborhood_analysis
空间邻域分析：空间邻居图 + cluster 共定位富集。参数：cluster_key("leiden"), n_rings(1) | 前提：需要空间坐标 + cluster

### run_svg_analysis
空间可变基因识别：使用 Moran's I 统计量。参数：n_top(50) | 前提：需要空间坐标

### run_cell_communication
细胞通讯分析：配体-受体互作推断（基于 OmniPath 数据库）。参数：cluster_key("leiden"), n_perms(200), alpha(0.05) | 前提：需要 raw counts + cluster

### run_spatial_domain
空间域检测：基于空间邻居图的图聚类。参数：resolution(1.0) | 前提：需要空间坐标

---

## 五、注释与文献 (3)

### run_enrichment_analysis
GO/KEGG/Reactome 富集分析（Enrichr API，需外网）。参数：cluster_key("leiden"), n_genes(30), db | 前提：需要先跑 run_marker_analysis

### run_knowledge_annotation
基因功能注释：GO 术语 + 通路（MyGene.info API，需外网）。参数：cluster_key("leiden"), n_genes(10), species("mouse")

### run_literature_search
PubMed 文献检索（需外网）。参数：query_genes(可选), topic(可选), n_papers(10)

---

## 六、多文件与报告 (4)

### detect_slices
自动检测数据中的多切片/多样本列

### run_multislice_comparison
同一文件内跨切片/样本对比。参数：slice_key（自动检测）| 前提：数据有 slice/sample 列

### merge_samples
合并多个已加载的 .h5ad 文件为统一数据集。前提：需要 load_multiple 加载 >=2 个文件

### cross_stage_comparison
跨发育阶段聚类对比分析。参数：cluster_key("leiden"), stage_key("stage"), resolution(1.0) | 前提：需要先跑 merge_samples

---

## 快捷调用

| 按钮 | 等价指令 | 包含工具 |
|------|---------|---------|
| 基础流程 | 跑基础分析流程 | overview-QC-preprocess-cluster-spatial-marker |
| 扩展分析 | 跑扩展分析 | neighbor-SVG-cell_comm |
| 聚类解释 | 解释聚类结果 | marker-enrichment |
| 生成报告 | 生成分析报告 | generate_report |
| 跨阶段 | 跨阶段对比分析 | load_multiple-merge-cross_stage |

## 参数速查

| 参数 | 默认值 | 说明 |
|------|--------|------|
| min_genes | 200 | 每个细胞最少基因数 |
| max_mito_pct | 20.0 | 线粒体比例上限 (%) |
| n_hvg | 2000 | 高变基因数 |
| n_pcs | 30 | 主成分数 |
| resolution | 1.0 | Leiden 聚类分辨率 |
| n_genes | 10 | marker 基因数 |
| n_perms | 200 | 细胞通讯置换检验次数 |
