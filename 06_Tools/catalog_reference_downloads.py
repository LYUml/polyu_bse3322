"""Build an offline reference index from verified download manifests."""
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / '02_References'

records = {}
for manifest in sorted(REF.glob('*下载清单.json')):
    obj = json.loads(manifest.read_text(encoding='utf-8'))
    for row in obj.get('files', []) if isinstance(obj, dict) else obj:
        records[row['path']] = row

if records.get('01_Assignment_Brief/BSE3322_Teaching_schedule_2026_v4.pdf', {}).get('status') == 'ok':
    records.pop('01_Assignment_Brief/Teaching_Schedule.pdf', None)

docs = ROOT / '06_Tools/02_Repository_Documentation'
docs.mkdir(parents=True, exist_ok=True)
for archive_path in (ROOT / '06_Tools/01_Repository_Snapshots').glob('*.zip'):
    project = archive_path.stem.rsplit('_', 1)[0]
    with zipfile.ZipFile(archive_path) as archive:
        prefix = archive.namelist()[0].split('/')[0] + '/'
        for name in archive.namelist():
            relative = name.removeprefix(prefix)
            if relative.lower() in ('readme.md', 'license', 'license.md', 'license.lesser', '.claude/skills/foam.md'):
                # Save external instructions as reference text, never as an active skill.
                target = docs / (project + '_' + relative.replace('/', '_').replace('\\', '_') + '.txt')
                target.write_bytes(archive.read(name))

# Repair links affected by the previous directory rename, using exact token only.
for folder in (REF, ROOT / '08_Project_Notes'):
    for path in folder.glob('*.md'):
        original = path.read_text(encoding='utf-8')
        fixed = original.replace('github.com/fire03_Models/', 'github.com/firemodels/')
        if fixed != original:
            path.write_text(fixed, encoding='utf-8')

groups = [
    ('作业与安排', '01_Assignment_Brief/'),
    ('课程材料', '02_References/01_Course_Materials/'),
    ('论文与书目', '02_References/02_Papers/'),
    ('香港排烟及关联规范', '02_References/03_HK_Regulations/'),
    ('FDS 官方文档', '02_References/04_FDS_Documentation/'),
    ('GitHub 源码快照', '06_Tools/01_Repository_Snapshots/'),
]
lines = ['# 本地下载资料目录', '', '更新：2026-11-13。只下载和整理，未安装工具、未建模、未运行仿真。', '',
         '来源、大小、SHA-256 和检查结果见 [完整清单](04_最终下载清单.json)。下载的 PDF 已验证可解析及页数；ZIP 已检查 CRC。加密课件只能核验文件容器和本地副本，不能读取内容。', '']
for title, prefix in groups:
    lines += ['## ' + title, '', '| 本地文件 | 大小 | 检查结果 |', '| --- | --- | --- |']
    for key, row in sorted(records.items()):
        if not key.startswith(prefix) or row['status'] != 'ok':
            continue
        file = ROOT / key
        link = '../' + key
        status = str(row['pages']) + ' 页 PDF' if 'pages' in row else '已保存并校验'
        if row.get('encrypted'):
            status = '**加密课件；需要课程密码，未读取内容**'
        if 'NOT_FULL_TEXT' in file.name:
            status = '**机构书目网页，非论文全文**'
        lines.append(f'| [{file.name}]({link}) | {row["bytes"]/1024/1024:.2f} MB | {status} |')
    lines += ['']

lines += ['## 尚未获取的资料', '',
          '- **Peng 2021 全文已补齐**：从 Google Scholar 的公开 PDF 入口下载，11 页，见上表。',
          '- **Yuen 2015 全文已补齐**：通过 PolyU Library / LibKey 和学校登录取得出版社 PDF，27 页（含封面），见上表。',
          '- **AL01、AL02 和最新版 Teaching Schedule v4 均已补齐**：由用户从 Canvas 下载并已完成本地归档、SHA-256 校验。详见 08_Project_Notes/资料补齐与下载问题_2026-11-13.md。',
          '- **Cap. 95B、Cap. 123J 的现行合并法例全文**：未成功获取离线正文，本地规范包不等于完整法例包。', '',
          '## 阅读顺序与使用边界', '',
          '1. W03 的排烟及烟帘案例、W04 的建模部分；AL03 已有本地副本，需原课程密码打开。',
          '2. FSD 2022 Code 第 5.23 节；4/96 烟控提交资料；2/2023 机械通风要求；BD 2024 Fire Safety Code。',
          '3. 4/2024 是 2022 Code 的勘误/中文版本通函；5/2026 针对自动泊车设施，不能直接当作本实验适用条款。',
          '4. 1/2025 和 6/2025 是废止通函清单，便于核对旧文件。6/2025 本身仍引用 4/96 Part I；这不表示 4/96 每个部分均未经修改。',
          '5. 本地 FDS 手册来自 PyroSim 安装目录，按随附版本使用，不冒充最新在线版。', '',
          '## GitHub 和 arXiv 复核结果', '',
          '| 项目 | 已落地的资料 | 适合借鉴什么 |',
          '| --- | --- | --- |',
          '| BULC MCP | 固定 commit 源码 ZIP、README 和许可参考文本 | 火灾软件 MCP 接口、知识规则、建模检查；桌面 app/solver 另需商业许可 |',
          '| PyFDS | 固定 commit 源码 ZIP、README 和许可参考文本 | 参数化生成 FDS 输入、执行管理；尚未安装或测试 |',
          '| fdsreader | 固定 commit 源码 ZIP、README 和许可参考文本 | FDS 二进制/CSV 后处理；许可按该快照中的文件核对 |',
          '| Foam-Agent | 固定 commit 源码 ZIP、README、许可、foam skill 参考文本；两篇 arXiv PDF | OpenFOAM 工作流与 MCP/skill 实现；不是 FDS/PyroSim 即插即用工具 |',
          '| FoamPilot | arXiv 2412.17146 论文全文 | FireFOAM 专用 agent 研究；尚未确认对应公开 agent 源码 |',
          '| Prometheus | 原作者公告链接见资料导航，未取得源码 | FDS 专业问答；作者说明不用于编写输入文件 |', '',
          '[本地项目 README、许可及 skill 参考文本](../06_Tools/02_Repository_Documentation/)；[源码 ZIP 与 commit 记录](../06_Tools/01_Repository_Snapshots/)。', '',
          'Foam-Agent 的 GitHub ZIP 可能包含 Git LFS 指针，未下载其模型权重、索引或其他运行依赖；未安装其 skill。外部 skill 以 .txt 保存，仅供审阅。', '',
          '检索中排除了 notDIRK/fds-mcp：其 FDS 指 FragDenStaat，与 Fire Dynamics Simulator 无关。没有把名称相同误作消防工具。', '',
          'GitHub 参考：[BULC](https://github.com/Meteor-Simulation/bulc-mcp)、[PyFDS](https://github.com/GraysonBellamy/pyfds)、[fdsreader](https://github.com/FireDynamics/fdsreader)、[Foam-Agent](https://github.com/csml-rpi/Foam-Agent)。',
          '论文参考：[FoamPilot](https://arxiv.org/abs/2412.17146)、[Foam-Agent](https://arxiv.org/abs/2505.04997)、[Foam-Agent 2.0](https://arxiv.org/abs/2509.18178)。', '']

(REF / '00_本地下载目录.md').write_text('\n'.join(lines), encoding='utf-8')
(REF / '04_最终下载清单.json').write_text(json.dumps({'date':'2026-11-13','files':list(records.values())}, ensure_ascii=False, indent=2), encoding='utf-8')
guide = REF / '00_资料导航.md'
text = guide.read_text(encoding='utf-8')
notice = '> **本地下载已更新：** 请先看 [本地下载目录](00_本地下载目录.md)。以下为此前的调查记录，其中“未下载/仅链接”等状态以本地下载目录及最终清单为准。\n\n'
if notice not in text:
    guide.write_text(notice + text, encoding='utf-8')
print(json.dumps({'ok':sum(r['status']=='ok' for r in records.values()),'failed':sum(r['status']!='ok' for r in records.values()),'bytes':sum(r.get('bytes',0) for r in records.values()),'extracted_reference_documents':len(list(docs.glob('*.txt')))}, ensure_ascii=False))
