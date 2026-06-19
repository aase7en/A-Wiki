---
type: source
title: "[Download](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/main/DeepS"
slug: deepseek-aideepseek-v4-pro-at-main
date_ingested: 2026-06-19
original_file: raw\deepseek-aiDeepSeek-V4-Pro at main.md
tags: [ai]
---

---
title: "deepseek-ai/DeepSeek-V4-Pro at main"
source: "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/blob/main/DeepSeek_V4.pdf"
author:
published: 2026-05-06
created: 2026-06-18
description: "We’re on a journey to advance and democratize artificial intelligence through open source and open science."
tags:
  - "clippings"
---
[Download](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/main/DeepSeek_V4.pdf?download=true)

Download with hf CLI

[History](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/commits/main/DeepSeek_V4.pdf) [Blame](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/blame/main/DeepSeek_V4.pdf) [Contribute](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/edit/main/DeepSeek_V4.pdf) [Delete](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/delete/main/DeepSeek_V4.pdf)

4.48 MB

DeepSeek-V4:  
Towards Highly Efficient Million-Token Context Intelligence  
DeepSeek-AI  
research@deepseek.com  
Abstract  
We present a preview version of DeepSeek-V4 series, including two strong Mixture-of-  
Experts (MoE) language models — DeepSeek-V4-Pro with 1.6T parameters (49B activated) and  
DeepSeek-V4-Flash with 284B parameters (13B activated) — both supporting a context length of  
one million tokens. DeepSeek-V4 series incorporate several key upgrades in architecture and op-  
timization: (1) a hybrid attention architecture that combines Compressed Sparse Attention (CSA)  
and Heavily Compressed Attention (HCA) to improve long-context efficiency; (2) Manifold-  
Constrained Hyper-Connections (m HC) that enhance conventional residual connections; (3)  
and the Muon optimizer for faster convergence and greater training stability. We pre-train  
both models on more than 32T diverse and high-quality tokens, followed by a comprehensive  
post-training pipeline that unlocks and further enhances their capabilities. DeepSeek-V4-Pro-  
Max, the maximum reasoning effort mode of DeepSeek-V4-Pro, redefines the state-of-the-art for  
open models, outperforming its predecessors in core tasks. Meanwhile, DeepSeek-V4 series are  
highly efficient in long-context scenarios. In the one-million-token context setting, DeepSeek-  
V4-Pro requires only 27% of single-token inference FLOPs and 10% of KV cache compared  
with DeepSeek-V3.2. This enables us to routinely support one-million-token contexts, thereby  
making long-horizon tasks and further test-time scaling more feasible. The model checkpoints  
are available at https://huggingface.co/collections/deepseek-ai/deepseek-v4.SimpleQA  
Verified  
(Pass @1)  
HLE  
(Pass @1)  
Apex  
Shortlist  
(Pass @1)  
Codeforces  
(Rating)  
SWE  
Verified  
(Resolved)  
Terminal  
Bench 2.0  
(Acc)  
Toolathlon  
(Pass @1)  
0  
20  
40  
60  
80  
100  
Accuracy / Pass@1 (%)  
57.9  
46.2 45.3  
75.6  
37.7 40.0 39.8  
44.4  
90.2  
85.9  
78.1  
89.1 3206 3168  
3052  
80.6 80.8 80.6  
67.9 65.4  
75.1  
68.5  
51.8  
47.2  
54.6  
48.8  
Knowledge & Reasoning Agentic Capabilities  
DeepSeek-V4-Pro-Max Claude-Opus-4.6-Max GPT-5.4-xHigh Gemini-3.1-Pro-High  
0 256 512 768 1024  
Token Position (K)  
0.0  
0.2  
0.4  
0.6  
0.8  
1.0  
1.2  
Single-Token FLOPs (T)  
3.7× lower  
9.8× lower  
DeepSeek-V3.2  
DeepSeek-V4-Pro  
DeepSeek-V4-Flash  
0 256 512 768 1024  
Sequence Length (K)  
0  
10  
20  
30  
40  
50  
Accumulated KV Cache (GB)  
9.5× smaller  
13.7× smaller  
DeepSeek-V3.2  
DeepSeek-V4-Pro  
DeepSeek-V4-Flash  
Figure 1 | Left: benchmark performance of DeepSeek-V4-Pro-Max and its counterparts.Right:  
inference FLOPs and KV cache size of DeepSeek-V4 series and DeepSeek-V3.2.

Contents  
1 Introduction 4  
2 Architecture 6  
2.1 Designs Inherited from DeepSeek-V3..........................7  
2.2 Manifold-Constrained Hyper-Connections......................7  
2.3 Hybrid Attention with CSA and HCA.........................9  
2.3.1 Compressed Sparse Attention..........................9  
2.3.2 Heavily Compressed Attention.........................11  
2.3.3 Other Details...................................12  
2.3.4 Efficiency Discussion...............................13  
2.4 Muon Optimizer.....................................14  
3 General Infrastructures 15  
3.1 Fine-Grained Communication-Computation Overlap in Expert Parallelism....15  
3.2 Flexible and Efficient Kernel Development with TileLang..............16  
3.3 High-Performance Batch-Invariant and Deterministic Kernel Libraries......18  
3.4 Training Framework...................................19  
3.4.1 Efficient Implementation of Muon.......................19  
3.4.2 Cost-Effective and Memory-Efficient Implementation of m HC.......20  
3.4.3 Contextual Parallelism for Long-Context Attention.............20  
3.4.4 Extended Automatic Differentiation for Flexible Activation Checkpointing 21  
3.5 Inference Framework...................................21  
3.5.1 KV Cache Structure and Management.....................21  
3.5.2 On-Disk KV Cache Storage...........................23  
4 Pre-Training 24  
4.1 Data Construction.....................................24  
4.2 Pre-Training Setups....................................24  
4.2.1 Model Setups...................................24  
4.2.2 Training Setups..................................25  
4.2.3 Mitigating Training Instability.........................26  
4.3 Evaluations........................................27  
4.3.1 Evaluation Benchmarks.............................27  
4.3.2 Evaluation Results................................27  
2

5 Post-Training 28  
5.1 Post-Training Pipeline..................................28  
5.1.1 Specialist Training................................28  
5.1.2 On-Policy Distillation..............................32  
5.2 Post-Training Infrastructures..............................33  
5.2.1 FP4 Quantization-Aware Training.......................33  
5.2.2 Efficient Teacher Scheduling for Full-Vocabulary OPD...........34  
5.2.3 Preemptible and Fault-Tolerant Rollout Service...............34  
5.2.4 Scaling RL Framework for Million-Token Context..............35  
5.2.5 Sandbox Infrastructure for Agentic AI.....................35  
5.3 Standard Benchmark Evaluation............................36  
5.3.1 Evaluation Setup.................................36  
5.3.2 Evaluation Results................................37  
5.4 Performance on Real-World Tasks...........................41  
5.4.1 Chinese Writing..................................41  
5.4.2 Search.......................................42  
5.4.3 White-Collar Task.................................42  
5.4.4 Code Agent....................................44  
6 Conclusion, Limitations, and Future Directions 44  
A Author List and Acknowledgment 54  
A.1 Author List.........................................54  
A.2 Acknowledgment.....................................55  
B Evaluation Details 55  
3

1\. Introduction  
The emergence of reasoning models (DeepSeek-AI, 2025; OpenAI, 2024c) has established a  
new paradigm of test-time scaling, driving substantial performance gains for Large Language  
Models (LLMs). However, this scaling paradigm is fundamentally constrained by the quadratic  
computational complexity of the vanilla attention mechanism (Vaswani et al., 2017), which  
creates a prohibitive bottleneck for ultra-long contexts and reasoning processes. Concurrently,  
the emergence of long-horizon scenarios and tasks — from complex agentic workflows to  
massive cross-document analysis — has also made efficient support for ultra-long contexts  
critical for future progress. While recent open-source efforts (Bai et al., 2025a; DeepSeek-AI,  
2024; MiniMax, 2025; Qwen, 2025) have advanced general capabilities, this core architectural  
inefficiency in handling ultra-long sequences remains a key impediment, limiting further gains  
from test-time scaling and hindering further exploration into long-horizon scenarios and tasks.  
In order to break the efficiency barrier in ultra-long contexts, we develop the DeepSeek-V4  
series, including the preview versions of DeepSeek-V4-Pro with 1.6T parameters (49B activated)  
and DeepSeek-V4-Flash with 284B parameters (13B activated). Through architectural innova-  
tions, DeepSeek-V4 series achieve a dramatic leap in computational efficiency for processing  
ultra-long sequences. This breakthrough enables efficient support for a context length of one  
million tokens, ushering in a new era of million-length contexts for next-generation LLMs. We  
believe our capability to efficiently handle ultra-long sequences unlocks the next frontier of  
test-time scaling, paves the way for deeper research into long-horizon tasks, and establishes a  
necessary foundation for exploring future paradigms like online learning.  
Compared with the DeepSeek-V3 architecture (DeepSeek-AI, 2024), DeepSeek-V4 series  
retain the DeepSeekMoE framework (Dai et al., 2024) and Multi-Token Prediction (MTP) strategy,  
while introducing several key innovations in architecture and optimization. To enhance long-  
context efficiency, we design a hybrid attention mechanism combining Compressed Sparse  
Attention (CSA) and Heavily Compressed Attention (HCA). CSA compresses the KV caches  
along the sequence dimension and then performs DeepSeek Sparse Attention (DSA) (DeepSeek-  
AI, 2025), whereas HCA applies more aggressive compression to the KV caches but keeps  
dense attention.To strengthen modeling capability, we incorporate Manifold-Constrained  
Hyper-Connections (m HC) (Xie et al., 2026) that upgrade conventional residual connections.  
Additionally, we introduce the Muon (Jordan et al., 2024; Liu et al., 2025) optimizer to the  
training of DeepSeek-V4 series, leading to faster convergence and improved training stability.  
To enable efficient training and inference for DeepSeek-V4 series as well as productive de-  
velopment, we introduce several infrastructure optimizations. First, we design and implement  
a single fused kernel for MoE modules that fully overlaps computation, communication, and  
memory access. Second, we employ TileLang (Wang et al., 2026), a Domain-Specific Language  
(DSL) to balance development productivity and runtime efficiency. Third, we provide efficient  
batch-invariant and deterministic kernel libraries to ensure bitwise reproducibility across train-  
ing and inference. Fourth, for the training framework, we extend the autograd framework with  
tensor-level checkpointing for fine-grained recomputation control; and we enhance training  
efficiency with a hybrid ZeRO strategy for the Muon optimizer, cost-effective m HC implemen-  
tations via recomputation and fused kernels, and two-stage contextual parallelism to manage  
compressed attention. Fifth, for the inference framework, we design a heterogeneous KV cache  
structure with on-disk storage strategies to enable efficient shared-prefix reuse. In addition,  
during the post-training stage, we incorporate FP4 quantization-aware training for MoE expert  
weights and the indexer QK path to reduce memory and computation.  
4

and storage, DeepSeek-V4 series achieve significantly lower inference FLOPs and a substantially  
reduced KV cache size compared with DeepSeek-V3.2, especially in long-context settings. The  
right part of Figure 1 demonstrates the estimated single-token inference FLOPs and accumulated  
KV cache size of DeepSeek-V3.2 and DeepSeek-V4 series. In the scenario of 1M-token context,  
even DeepSeek-V4-Pro, which has a larger number of activated parameters, attains only 27%  
of the single-token FLOPs (measured in equivalent FP8 FLOPs) and 10% of the KV cache  
size relative to DeepSeek-V3.2. Furthermore, DeepSeek-V4-Flash, with its smaller number of  
activated parameters, pushes efficiency even further: in the 1M-token context setting, it achieves  
only 10% of the single-token FLOPs and 7% of the KV cache size compared with DeepSeek-V3.2.  
Additionally, for DeepSeek-V4 series, the routed expert parameters utilize FP4 precision. While  
the peak FLOPs for FP4 × FP8 operations are currently the same as FP8 × FP8 on existing  
hardware, they can theoretically be implemented to be 1 / 3 more efficient on future hardware,  
which will further enhance the efficiency of DeepSeek-V4 series.  
During pre-training, we train DeepSeek-V4-Flash on 32T tokens and DeepSeek-V4-Pro on 33T  
tokens, respectively. After pre-training, these two models can natively and efficiently support  
1M-length contexts. In our internal evaluations, DeepSeek-V4-Flash-Base already surpasses  
DeepSeek-V3.2-Base across a majority of benchmarks with its more parameter-efficient design.  
DeepSeek-V4-Pro-Base further extends this advantage to set a new performance standard among  
DeepSeek foundation models, achieving comprehensive superiority across reasoning, coding,  
long-context, and world knowledge tasks.  
The post-training pipeline of DeepSeek-V4 series features a two-stage paradigm: the inde-  
pendent cultivation of domain-specific experts, followed by unified model consolidation via  
on-policy distillation (Gu et al., 2024; Lu and Lab, 2025). Initially, for each target domain — such  
as mathematics, coding, agent, and instruction following — a separate expert model is trained  
independently. The base model first undergoes Supervised Fine-Tuning (SFT) on high-quality,  
domain-specific data to establish foundational capabilities. Subsequently, Reinforcement Learn-  
ing (RL) is applied using Group Relative Policy Optimization (GRPO) (DeepSeek-AI, 2025),  
which further optimizes the model for domain-aligned behaviors guided by reward models  
tailored to specific success criteria. This phase yields a diverse set of specialized experts, each  
excelling in its respective field. Finally, to integrate these distinct proficiencies, a single unified  
model is trained through on-policy distillation, wherein the unified model acts as the student  
learning to optimize the reverse KL loss with teacher models.  
Summary of Core Evaluation Results  
• Knowledge: In assessments of broad world knowledge, DeepSeek-V4-Pro-Max, the maxi-  
mum reasoning effort mode of DeepSeek-V4-Pro, significantly outperforms leading open-  
source models on the SimpleQA (OpenAI, 2024d) and Chinese-SimpleQA (He et al., 2024)  
benchmarks. Regarding educational knowledge — evaluated via MMLU-Pro (Wang et al.,  
2024b), HLE (Phan et al., 2025), and GPQA (Rein et al., 2023) — DeepSeek-V4-Pro-Max  
shows a marginal lead over its open-source counterparts. DeepSeek-V4-Pro-Max has  
significantly closed the gap with the leading proprietary model, Gemini-3.1-Pro, despite  
still trailing it in these knowledge-based evaluations.  
• Reasoning: Through the expansion of reasoning tokens, DeepSeek-V4-Pro-Max demon-  
strates superior performance relative to GPT-5.2 and Gemini-3.0-Pro on standard reasoning  
benchmarks. Nevertheless, its performance falls marginally short of GPT-5.4 and Gemini-  
3.1-Pro, suggesting a developmental trajectory that trails state-of-the-art frontier models by  
approximately 3 to 6 months. Furthermore, DeepSeek-V4-Flash-Max achieves comparable  
5

Input Tokens  
Embedding  
CSA / HCA  
Prediction Head  
MTP Modules  
LM Loss  
MTP Loss  
Residual Mixing  
Pre-Block Mixing  
Post-Block Mixing  
Transformer Block × 𝐿𝐿  
DeepSeekMoE  
Residual Mixing  
Pre-Block Mixing  
Post-Block Mixing Figure 2 | Overall architecture of DeepSeek-V4 series. We use hybrid CSA (Compressed Sparse  
Attention) and HCA (Heavily Compressed Attention) for attention layers, DeepSeekMoE for  
feed-forward layers, and strengthen conventional residual connections with m HC.  
performance to GPT-5.2 and Gemini-3.0-Pro, establishing itself as a highly cost-effective  
architecture for complex reasoning tasks.  
• Agent: On public benchmarks, DeepSeek-V4-Pro-Max is on par with leading open-source  
models, such as Kimi-K2.6 and GLM-5.1, but slightly worse than frontier closed models.  
In our internal evaluation, DeepSeek-V4-Pro-Max outperforms Claude Sonnet 4.5 and  
approaches the level of Opus 4.5.  
• Long-Context: DeepSeek-V4-Pro-Max delivers strong results on synthetic and real use  
cases with a 1-million-token context window, surpassing even Gemini-3.1-Pro on academic  
benchmarks.  
• DeepSeek-V4-Pro v.s. DeepSeek-V4-Flash: DeepSeek-V4-Flash-Max exhibits lower per-  
formance in knowledge evaluations due to its smaller parameter scale.However, it  
achieves comparable results on reasoning tasks when allocated a larger thinking bud-  
get. In agent evaluations, while DeepSeek-V4-Flash-Max matches the performance of  
DeepSeek-V4-Pro-Max on several benchmarks, it still trails its larger counterpart on more  
complex, high-difficulty tasks.  
2\. Architecture  
Overall, DeepSeek-V4 series retain the Transformer (Vaswani et al., 2017) architecture and Multi-  
Token Prediction (MTP) modules (DeepSeek-AI, 2024; Gloeckle et al., 2024), while introducing  
several key upgrades over DeepSeek-V3: (1) firstly, we introduce the Manifold-Constrained  
Hyper-Connections (m HC) (Xie et al., 2026) to strengthen conventional residual connections;  
6

(2) secondly, we design a hybrid attention architecture, which greatly improves long-context  
efficiency through Compressed Sparse Attention and Heavily Compressed Attention. (3) thirdly,  
we employ Muon (Jordan et al., 2024; Liu et al., 2025) as the optimizer. For the Mixture-of-  
Experts (MoE) components, we still adopt the DeepSeekMoE (Dai et al., 2024) architecture, with  
only minor adjustments from DeepSeek-V3. The Multi-Token Prediction (MTP) (DeepSeek-AI,  
2024; Gloeckle et al., 2024; Li et al., 2024; Qi et al., 2020) configuration remains identical to  
that of DeepSeek-V3. All other unspecified details follow the settings established in DeepSeek-  
V3 (DeepSeek-AI, 2024). Figure 2 illustrates the overall architecture of DeepSeek-V4, and the  
details are described below.  
2.1. Designs Inherited from DeepSeek-V3  
Mixture-of-Experts.As previous DeepSeek-series models (DeepSeek-AI, 2024; DeepSeek-AI,  
2024), DeepSeek-V4 series also adopt the DeepSeekMoE paradigm (Dai et al., 2024) for Feed-  
Forward Networks (FFNs), which sets fine-grained routed experts and shared experts. Different  
from DeepSeek-V3, we change the activation function that computes the affinity scores from  
Sigmoid (·) into Sqrt (Softplus (·)). For load balancing, we also employ the auxiliary-loss-free  
strategy (DeepSeek-AI, 2024; Wang et al., 2024a), augmented by a slight sequence-wise balance  
loss that prevents extreme imbalance within individual sequences. For DeepSeek-V4, we remove  
the constraint on the number of routing target nodes, and carefully redesign the parallelism  
strategy to maintain training efficiency. Furthermore, compared with DeepSeek-V3, we replace  
the dense FFN layers in the initial several Transformer blocks with MoE layers that employ  
Hash routing (Roller et al., 2021). The Hash routing strategy determines the target experts of  
each token according to a predefined hash function with regard to the input token ID.  
Multi-Token Prediction.As DeepSeek-V3, DeepSeek-V4 series also set MTP modules and  
objectives. Given that the MTP strategy has been validated in DeepSeek-V3, we adopt the same  
strategy for DeepSeek-V4 series without modification.  
2.2. Manifold-Constrained Hyper-Connections  
As shown in Figure 2, DeepSeek-V4 series incorporate Manifold-Constrained Hyper-Connections  
(m HC) (Xie et al., 2026) to strengthen the conventional residual connections between adjacent  
Transformer blocks. Compared with naive Hyper-Connections (HC) (Zhu et al., 2025), the core  
idea of m HC is to constrain the residual mapping onto a specific manifold, and thus enhance the  
stability of signal propagation across layers while preserving model expressivity. This subsection  
briefly introduces the standard HC and describes how we design m HC for stable training.  
Standard Hyper-Connections.The standard HC expands the width of the residual stream  
by a factor of 𝑛 hc. Specifically, the shape of the residual stream is expanded from R 𝑑 to R 𝑛 hc × 𝑑,  
where 𝑑 is the hidden size of the actual layer input. Let 𝑋 𝑙 \= \[x 𝑙,1;...;x 𝑙,𝑛 hc\] 𝑇 ∈ R 𝑛 hc × 𝑑 be the  
residual state before the 𝑙 \-th layer. HC introduces three linear mappings: an input mapping  
𝐴 𝑙 ∈ R 1 × 𝑛 hc, a residual transformation 𝐵 𝑙 ∈ R 𝑛 hc × 𝑛 hc, and an output mapping 𝐶 𝑙 ∈ R 𝑛 hc × 1. The  
update of the residual state is then formulated as:  
𝑋 𝑙 + 1 \= 𝐵 𝑙 𝑋 𝑙 + 𝐶 𝑙 F 𝑙 (𝐴 𝑙 𝑋 𝑙),(1)  
where F 𝑙 denotes the 𝑙 \-th layer (e.g., an MoE layer), whose input and output shapes are both  
R 𝑑. Note that the actual layer input 𝐴 𝑙 𝑋 𝑙 ∈ R 𝑑 is also 𝑑 \-dimensional, so the expanded residual  
7

width does not influence the design of the inner layers. HC decouples the residual width from  
the actual hidden size, offering a complementary scaling axis with minimal computational  
overhead, as 𝑛 hc is typically much smaller than the hidden size 𝑑. However, even though HC  
has demonstrated potential in improving model performance, we find that the training will  
frequently exhibit numerical instability when stacking multiple layers, which hinders the scaling  
of HC.  
Manifold-Constrained Residual Mapping.The core innovation of m HC is to constrain the  
residual mapping matrix 𝐵 𝑙 to the manifold of doubly stochastic matrices (the Birkhoff polytope)  
M, and thus enhance the stability of signal propagation across layers:  
𝐵 𝑙 ∈ M ≔ { 𝑀 ∈ R 𝑛 × 𝑛 | 𝑀 1 𝑛 \= 1 𝑛,1 𝑇  
𝑛 𝑀 \= 1 𝑇  
𝑛,𝑀 ⩾ 0 }.(2)  
This constraint ensures that the spectral norm of the mapping matrix ∥ 𝐵 𝑙 ∥ 2 is bounded by 1, so  
the residual transformation is non-expansive, which increases the numerical stability during both  
the forward pass and backpropagation. Besides, the set M is closed under multiplication, which  
guarantees stability in the scenarios of deep stacks of m HC. In addition, the input transformation  
𝐴 𝑙 and output transformation 𝐶 𝑙 are also constrained to be non-negative and bounded via a  
Sigmoid function to avoid the risk of signal cancellation.  
Dynamic Parameterization.The parameters of three linear mappings are dynamically gen-  
erated, which are decomposed into a dynamic (input-dependent) component and a static  
(input-independent) component. Given the input 𝑋 𝑙 ∈ R 𝑛 hc × 𝑑, it is first flattened and normal-  
ized:ˆ 𝑋 𝑙 \= RMSNorm (vec (𝑋 𝑙)) ∈ R 1 × 𝑛 hc 𝑑. Then, we follow the conventional HC to generate the  
unconstrained raw parameters ˜ 𝐴 𝑙 ∈ R 1 × 𝑛 hc, ˜ 𝐵 𝑙 ∈ R 𝑛 hc × 𝑛 hc, and ˜ 𝐶 𝑙 ∈ R 𝑛 hc × 1:  
˜ 𝐴 𝑙 \= 𝛼 pre  
𝑙 · (ˆ 𝑋 𝑙 𝑊 pre  
𝑙) + 𝑆 pre  
𝑙,(3)  
˜ 𝐵 𝑙 \= 𝛼 res  
𝑙 · Mat (ˆ 𝑋 𝑙 𝑊 res  
𝑙) + 𝑆 res  
𝑙,(4)  
˜ 𝐶 𝑙 \= 𝛼 post  
𝑙 · (ˆ 𝑋 𝑙 𝑊 post  
𝑙) 𝑇 + 𝑆 post  
𝑙,(5)  
where 𝑊 pre  
𝑙,𝑊 post  
𝑙 ∈ R 𝑛 hc 𝑑 × 𝑛 hc and 𝑊 res  
𝑙 ∈ R 𝑛 hc 𝑑 × 𝑛 2  
hc are learnable parameters for generating the  
dynamic components;Mat (·) reshapes a vector of size 1 × 𝑛 2  
hc into a matrix of size 𝑛 hc × 𝑛 hc;  
𝑆 pre  
𝑙 ∈ R 1 × 𝑛 hc,𝑆 post  
𝑙 ∈ R 𝑛 hc × 1, and 𝑆 res  
𝑙 ∈ R 𝑛 hc × 𝑛 hc are learnable static biases; and 𝛼 pre  
𝑙,𝛼 res  
𝑙,𝛼 post  
𝑙 ∈ R  
are learnable gating factors initialized to small values.  
Applying Parameter Constraints.After obtaining the unconstrained raw parameters ˜ 𝐴 𝑙,˜ 𝐵 𝑙,˜ 𝐶 𝑙,  
we then apply constraints described earlier to them to enhance the numerical stability. To be  
specific, for the input and output mappings, we employ a Sigmoid function 𝜎 (·) to ensure their  
non-negativity and boundedness:  
𝐴 𝑙 \= 𝜎 (˜ 𝐴 𝑙),(6)  
𝐶 𝑙 \= 2 𝜎 (˜ 𝐶 𝑙).(7)  
As for the residual mapping ˜ 𝐵 𝑙, we project it onto the manifold of doubly stochastic matrices M.  
This is achieved by the Sinkhorn-Knopp algorithm, which first applies an exponential function  
to ˜ 𝐵 𝑙 to ensure positivity, getting 𝑀 (0) \= exp (˜ 𝐵 𝑙), and then iteratively performs column and row  
normalization:  
𝑀 (𝑡) \= T 𝑟 (T 𝑐 (𝑀 (𝑡 − 1))),(8)  
where T 𝑟 and T 𝑐 denote row and column normalization, respectively. This iteration converges to  
a constrained doubly stochastic matrix 𝐵 𝑙 \= 𝑀 (𝑡 max). We choose 𝑡 max \= 20 as a practical value.  
8

… Hidden States of KV Tokens  
… Compressed  
Indexer Keys  
Hidden State of Query Token  
Multi-Query  
Attention  
Compressed  
KV Entries …  
Top-k  
Selector  
Selected  
Compressed  
KV Entries  
…  
Shared Key-Value Multi-Query Attention  
Indexer Queries Queries  
Sliding Window  
KV Entries  
Concatenation  
Token-Level  
Compressor  
…  
Token-Level  
Compressor  
Lightning Indexer  
Index Scores Figure 3 | Core architectures of CSA. It compresses the number of KV entries to 1  
𝑚 times, and  
then applies DeepSeek Sparse Attention for further acceleration. Additionally, a small set of  
sliding window KV entries is combined with the selected compressed KV entries to enhance  
local fine-grained dependencies.  
2.3. Hybrid Attention with CSA and HCA  
As the context length reaches extreme scales, the attention mechanism emerges as the dominant  
computational bottleneck in a model.For DeepSeek-V4, we design two efficient attention  
architectures — Compressed Sparse Attention (CSA) and Heavily Compressed Attention (HCA)  
— and employ their interleaved hybrid configuration, which substantially reduces the compu-  
tational cost of attention in long-text scenarios. CSA integrates both compression and sparse  
attention strategies: it first compresses the Key-Value (KV) cache of every 𝑚 tokens into one  
entry, and then applies DeepSeek Sparse Attention (DSA) (DeepSeek-AI, 2025) where each query  
token attends to only 𝑘 compressed KV entries. HCA aims for extreme compression by consol-  
idating the KV cache of every 𝑚 ′ (≫ 𝑚) tokens into a single entry. The hybrid architecture of  
CSA and HCA remarkably improves the long-context efficiency of DeepSeek-V4 series, making  
one-million-token context feasible in practice. This subsection describes the core techniques  
of our hybrid attention architecture, and we also provide an open-source implementation 1 to  
specify more details unambiguously.  
2.3.1. Compressed Sparse Attention  
The core architecture of CSA is illustrated in Figure 3, which first compresses the KV cache of each  
𝑚 tokens into one entry, and then applies DeepSeek Sparse Attention for further acceleration.  
Compressed Key-Value Entries.Let 𝐻 ∈ R 𝑛 × 𝑑 be a sequence of input hidden states, where  
𝑛 is the sequence length and 𝑑 is the hidden size. CSA first computes two series of KV entries  
𝐶 𝑎,𝐶 𝑏 ∈ R 𝑛 × 𝑐 and their corresponding compression weights 𝑍 𝑎,𝑍 𝑏 ∈ R 𝑛 × 𝑐, where 𝑐 is the head  
1 https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/tree/main/inference  
9

dimension:  
𝐶 𝑎 \= 𝐻 · 𝑊 𝑎𝐾𝑉,𝐶 𝑏 \= 𝐻 · 𝑊 𝑏𝐾𝑉,(9)  
𝑍 𝑎 \= 𝐻 · 𝑊 𝑎𝑍,𝑍 𝑏 \= 𝐻 · 𝑊 𝑏𝑍,(10)  
where 𝑊 𝑎𝐾𝑉,𝑊 𝑏𝐾𝑉,𝑊 𝑎𝑍,𝑊 𝑏𝑍 ∈ R 𝑑 × 𝑐 are trainable parameters. Next, each 𝑚 KV entries in 𝐶 𝑎 and  
𝐶 𝑏 will be compressed into one entry according to their compression weights and learnable  
positional biases 𝐵 𝑎,𝐵 𝑏 ∈ R 𝑚 × 𝑐, producing 𝐶 Comp ∈ R 𝑛  
𝑚 × 𝑐. Each compressed entry 𝐶 Comp  
𝑖 ∈ R 𝑐 is  
computed by  
\[𝑆 𝑎  
𝑚𝑖:𝑚 (𝑖 + 1) − 1;𝑆 𝑏  
𝑚 (𝑖 − 1):𝑚𝑖 − 1\] \= Softmax row (\[𝑍 𝑎  
𝑚𝑖:𝑚 (𝑖 + 1) − 1 + 𝐵 𝑎;𝑍 𝑏  
𝑚 (𝑖 − 1):𝑚𝑖 − 1 + 𝐵 𝑏\]),(11)  
𝐶 Comp  
𝑖 \=  
𝑚 (𝑖 + 1) − 1 ∑︁  
𝑗 \= 𝑚𝑖  
𝑆 𝑎  
𝑗 ⊙ 𝐶 𝑎  
𝑗 +  
𝑚𝑖 − 1 ∑︁  
𝑗 \= 𝑚 (𝑖 − 1)  
𝑆 𝑏  
𝑗 ⊙ 𝐶 𝑏  
𝑗,(12)  
where ⊙ denotes the Hadamard product;Softmax row (·) denotes the softmax operation along  
the row dimension, which performs normalization across the total of 2 𝑚 elements from both  
𝑍 𝑎 and 𝑍 𝑏. When 𝑖 \= 0,𝑍 𝑏  
𝑚 (𝑖 − 1):𝑚𝑖 − 1 is padded with negative infinity and 𝐶 𝑏  
𝑚 (𝑖 − 1):𝑚𝑖 − 1 is padded  
with zeros. Note that each 𝐶 Comp  
𝑖 is derived from 2 𝑚 KV entries, but the indexes of 𝐶 𝑏 used for  
𝐶 Comp  
𝑖 and the indexes of 𝐶 𝑎 used for 𝐶 Comp  
𝑖 − 1 are overlapped. Therefore, CSA in fact compresses  
the sequence length to 1  
𝑚 times.  
Lightning Indexer for Sparse Selection.After obtaining the compressed KV entries 𝐶 Comp,  
CSA applies the DSA strategy to select top-k compressed KV entries for core attention. First,  
CSA performs the same compression operation used for 𝐶 Comp to get compressed indexer keys  
𝐾 IComp ∈ R 𝑛  
𝑚 × 𝑐 𝐼  
, where 𝑐 𝐼 is the indexer head dimension. Then, for a query token 𝑡, we produce  
the indexer queries { q 𝐼  
𝑡,1;q 𝐼  
𝑡,2;...;q 𝐼  
𝑡,𝑛 𝐼  
ℎ  
} in a low-rank manner:  
c 𝑄  
𝑡 \= h 𝑡 · 𝑊 𝐷𝑄,(13)  
\[q 𝐼  
𝑡,1;q 𝐼  
𝑡,2;...;q 𝐼  
𝑡,𝑛 𝐼  
ℎ  
\] \= q 𝐼  
𝑡 \= c 𝑄  
𝑡 · 𝑊 𝐼𝑈𝑄,(14)  
where h 𝑡 ∈ R 𝑑 is the input hidden state of the query token 𝑡;c 𝑄  
𝑡 ∈ R 𝑑 𝑐 is the compressed  
latent vector for queries;𝑑 𝑐 denotes the query compression dimension;𝑛 𝐼  
ℎ denotes the number  
of indexer query heads;𝑊 𝐷𝑄 ∈ R 𝑑 × 𝑑 𝑐 and 𝑊 𝐼𝑈𝑄 ∈ R 𝑑 𝑐 × 𝑐 𝐼 𝑛 𝐼  
ℎ are the down-projection and up-  
projection matrices for indexer queries, respectively. Next, the index score 𝐼 𝑡,𝑠 ∈ R between the  
query token 𝑡 and a preceding compressed block 𝑠 (𝑠 < Floor (𝑡  
𝑚)) is computed by  
\[𝑤 𝐼  
𝑡,1;𝑤 𝐼  
𝑡,2;...;𝑤 𝐼  
𝑡,𝑛 𝐼  
ℎ  
\] \= w 𝐼  
𝑡 \= h 𝑡 · 𝑊 𝑤,(15)  
𝐼 𝑡,𝑠 \=  
𝑛 𝐼  
ℎ ∑︁  
ℎ \= 1  
𝑤 𝐼  
𝑡,ℎ · ReLU  
  
q 𝐼  
𝑡,ℎ · 𝐾 IComp  
𝑠  
  
,(16)  
where 𝑊 𝑤 ∈ R 𝑑 × 𝑛 𝐼  
ℎ is a learnable matrix;𝑤 𝐼  
𝑡,ℎ ∈ R is the weight of the ℎ \-th indexer head. For a  
query token 𝑡, given its index scores 𝐼 𝑡,:, we employ a top-k selector to selectively retain a subset  
of compressed KV entries C SprsComp  
𝑡 for subsequent core attention:  
C SprsComp  
𝑡 \=  
n  
𝐶 Comp  
𝑠 𝐼 𝑡,𝑠 ∈ Top-k (𝐼 𝑡,:)  
o  
.(17)  
10

### Xet Pointer Details

( [Raw pointer file](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/raw/main/DeepSeek_V4.pdf) )

Xet hash:

60ba3f8de5d5172b5f3230b024eff941ac2ca747c301035124a2787e6169be2b

Size of remote file:

4.48 MB

·

SHA256:

8a03dadae71894de1515da33e296f0df1dbeed3e7f4bf0badd087f9af77f29e9

Xet efficiently stores Large Files inside Git, intelligently splitting files into unique chunks and accelerating uploads and downloads. [More info](https://huggingface.co/join/xet).
