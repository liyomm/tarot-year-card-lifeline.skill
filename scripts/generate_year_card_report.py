#!/usr/bin/env python3
"""Generate a simplified-Chinese Mary K. Greer Tarot Year Card report and SVG charts."""

from __future__ import annotations

import argparse
import datetime as dt
import html
from pathlib import Path
import re
import shutil
import sys
from collections import Counter, defaultdict

# Content tables are intentionally kept beside the deterministic calculator.  They are
# source-scoped in references/source-index.md; prose must never present synthesis as a
# quotation from any of the three source systems.

CARDS = {
    1: ("I", "魔术师", "主动运用资源，把想法变成可执行的第一步", "避免分心、过度承诺或只靠技巧；先确认动机与事实"),
    2: ("II", "女祭司", "放慢外在反应，倾听直觉并观察尚未显现的信息", "不要把沉默等同于答案；重要事项仍需核实证据"),
    3: ("III", "皇后", "培育身体、关系与创造项目，让生活长出可持续成果", "避免过度照顾他人而耗尽自己，也要留心消费与身体信号"),
    4: ("IV", "皇帝", "建立结构、边界与责任次序，把长期目标落实为制度", "避免僵化与控制欲；检查规则是否仍然服务于真实需要"),
    5: ("V", "教皇", "向体系、传统或导师学习，并形成自己的价值准则", "尊重经验但不盲从权威，也别为了合群压下疑问"),
    6: ("VI", "恋人", "围绕真实价值做选择，并在关系中练习平等与坦诚", "避免讨好、摇摆或把决定交给别人；选择也意味着承担"),
    7: ("VII", "战车", "确定方向，协调不同诉求，以意志和纪律向前推进", "避免急于证明、硬冲和过劳；速度不能替代方向"),
    8: ("VIII", "力量", "以耐心和温柔的勇气面对本能、恐惧与压力", "避免压抑情绪或逞强透支；真正的力量也包含求助"),
    9: ("IX", "隐士", "向内整理经验，在独立学习与反思中形成智慧", "避免把谨慎变成隔绝或完美主义；独处需要有出口"),
    10: ("X", "命运之轮", "识别周期与转折，借变化重新调整位置和策略", "不要把一切归因于运气；为波动保留缓冲与预案"),
    11: ("XI", "正义", "审视因果、责任与公平，让决定经得起事实检验", "留意合同、记录与程序，也避免苛刻审判自己或他人"),
    12: ("XII", "吊人", "暂停旧路径，换角度理解处境，并为必要转变留白", "区分主动停顿与消极拖延；为停顿设置期限和复盘点"),
    13: ("XIII", "死神", "完成告别与更新，让已经结束的阶段真正退出", "不要因害怕失去而拖延收尾，也别在情绪高峰作不可逆决定"),
    14: ("XIV", "节制", "调和差异、修复节奏，在持续试验中找到合适配比", "避免极端摆动与一味迁就；稳定来自持续微调"),
    15: ("XV", "恶魔", "直视欲望、依附与权力关系，收回被惯性占据的选择权", "留意成瘾、债务、控制与羞耻循环；先命名诱因再找替代方案"),
    16: ("XVI", "高塔", "让不再可靠的结构显露问题，并以真实为基础重建", "先顾安全与应急安排；把震荡拆成可处理的问题"),
    17: ("XVII", "星星", "恢复希望与长期愿景，以真实姿态重新连接世界", "避免只沉浸理想或过度暴露自己；愿景需要日常执行"),
    18: ("XVIII", "月亮", "穿越模糊与情绪波动，辨认直觉、投射和恐惧", "信息不清时避免仓促承诺；核实传闻并照顾睡眠与焦虑"),
    19: ("XIX", "太阳", "让成果被看见，享受清晰、活力与真诚连接", "避免过度自信、过度曝光或忽视休息与他人贡献"),
    20: ("XX", "审判", "回顾长周期，整合旧经验并回应更深的召唤", "放下无休止的自责与外界评判，妥善处理遗留事项"),
    21: ("XXI", "世界", "完成整合与收官，看见自己在更大系统中的位置", "完成后也要休息、归档与交接，为新周期留下空间"),
    22: ("22／0", "愚人", "带着开放心态进入未知，允许新的生命经验发生", "自由需要基本安全意识；给冒险设置底线与回程方案"),
}

ENGLISH = {
    1: "The Magician", 2: "The High Priestess", 3: "The Empress", 4: "The Emperor",
    5: "The Hierophant", 6: "The Lovers", 7: "The Chariot", 8: "Strength",
    9: "The Hermit", 10: "Wheel of Fortune", 11: "Justice", 12: "The Hanged Man",
    13: "Death", 14: "Temperance", 15: "The Devil", 16: "The Tower",
    17: "The Star", 18: "The Moon", 19: "The Sun", 20: "Judgement",
    21: "The World", 22: "The Fool",
}

APPENDIX_NAMES = {
    8: "力量／欲 / Strength / Lust", 11: "正义／调整 / Justice / Adjustment",
    14: "节制／艺术 / Temperance / Art", 20: "审判／永恒 / Judgement / Aeon",
    21: "世界／宇宙 / The World / Universe",
}

ANNUAL_THEMES = {
    1: "集中注意力、写作、沟通、魔法，以及运用心灵力量克服一切，以及任何与心智上努力相关的事物。",
    2: "独立、直觉或心灵上的发展、与女性的关系、自我滋养。",
    3: "创造力、孕育、滋养他人、与女性的关系、喜爱愉悦和美丽的事物，具有魅力和吸引人的。",
    4: "开始新事物、开拓、建造、建构、充满自信与权威、奠定基础或稳固基础、与男性的关系。",
    5: "学习与教导、听与说、从事与社会架构或阶级相关工作、理解‘系统’。",
    6: "任何关系、与感情相关的重大抉择、作决定并接受随之而来的责任。",
    7: "向世界证明自己、搬迁、旅行、学习保护——照顾自己与他人、设定与达成目标。",
    8: "创意的渴望、强烈的热情及欲望、引发强大力量及耐力的挑战、处理愤怒情绪。",
    9: "孤独、内省、从经验中或向榜样学习、完美、追求、完成计划。",
    10: "重要的变动——关于居所、工作、观点，以及完成一个周期并开始新周期、运气和命运、名利及财富。",
    11: "法律及财务方面的考量、平衡与和谐、学习以真实的自己与人相处、伙伴关系、契约。",
    12: "处理自己的难题、自我牺牲、磨难、酗酒及成瘾问题、放弃既有的观念、态度、信仰、获得新观点。",
    13: "放下某些东西、割舍陈旧模式以容纳新的成长、重生与再生、痛苦、深究事物底层、研究。",
    14: "促进健康与治疗的方法、测试及尝试自己的信仰与哲学、创造性组合。",
    15: "权力斗争、操纵、保持幽默感、引发不安、质疑权威、强烈的性欲。",
    16: "涤净——运动、节食、断食、大扫除、愤怒与痛苦、卸除或毁灭老旧而不必要的架构。",
    17: "确认自己的目标、理想和人道主义思想，并采取行动；意识到地球是万物的本质，渴望能够疗愈她。",
    18: "具丰富的想象力及梦境能力、被未知欲望牵引的感觉、业力关系。",
    19: "认可、达成主要目标、婚姻或生育、自我价值感。",
    20: "从自己和他人身上处理与判断、批判和评价相关的议题；得到新的信念、世界观与理解；重生、处理死亡和转化的议题。",
    21: "学习与自己的局限共舞、在限制或框架内做事、无穷的可能性。",
    22: "探险、旅行、大胆的、对新体验的开放心态。",
}

# Compact wording used in the annual table and current-year summary.
SHORT = {
    1: ("聚焦意志，启动行动", "避免分心与操控"), 2: ("静观内在，辨认直觉", "重要信息仍需核实"),
    3: ("滋养关系与创造", "避免过度付出"), 4: ("建立结构与边界", "避免僵化控制"),
    5: ("学习传统，形成准则", "尊重经验但不盲从"), 6: ("依价值作出选择", "避免讨好与摇摆"),
    7: ("协调力量，明确方向", "避免急进与过劳"), 8: ("以温柔勇气应对压力", "避免压抑与逞强"),
    9: ("独处反思，沉淀智慧", "避免封闭孤立"), 10: ("识别周期，顺势调整", "不要只归因于运气"),
    11: ("审视因果与公平", "避免苛刻评判"), 12: ("暂停旧路，转换视角", "避免无期限拖延"),
    13: ("完成告别，允许更新", "避免执着旧阶段"), 14: ("调和差异，修复节奏", "避免极端摆动"),
    15: ("看见依附，收回选择", "留意成瘾与控制"), 16: ("看清裂缝，重建基础", "先顾安全与缓冲"),
    17: ("恢复希望，连接愿景", "理想需要日常落实"), 18: ("穿越模糊，辨认投射", "信息不清勿仓促"),
    19: ("展现成果，真诚连接", "避免过度曝光"), 20: ("整合过去，回应召唤", "放下反复自责"),
    21: ("完成整合，妥善收官", "为新周期留空间"), 22: ("开放探索，进入未知", "冒险仍需安全底线"),
}

CONSTELLATIONS = {
    1: ("魔术师星群", (19, 10, 1), "意志与专注力"), 2: ("女祭司星群", (20, 11, 2), "透过直觉平衡判断"),
    3: ("皇后星群", (21, 12, 3), "爱与创造性想象"), 4: ("皇帝星群", (22, 13, 4), "生命力与权力的展现"),
    5: ("教皇星群", (14, 5), "教导与学习"), 6: ("恋人星群", (15, 6), "关联与选择"),
    7: ("战车星群", (16, 7), "经由改变而掌握"), 8: ("力量星群", (17, 8), "勇气与自尊"),
    9: ("隐士星群", (18, 9), "内省与个人修养"),
}

COMBINATION_ANALYSES = {
    1: "你倾向先集中意志、命名目标，再让资源围绕目标排列。太阳与命运之轮放大可见度和转折感：优势是启动、表达与创造机会；压力下则可能把价值感系在成果、认可或掌控感上。导师课题是分辨真正的意图，在变化中保持专注，而不是以技巧代替诚实。",
    2: "你的核心方式是先感受、观察，再作判断。正义与审判让直觉不只是感受，也要求事实、责任与长周期复盘：优势是洞察细微关系并保持公平；压力下可能迟疑、沉默或过度自我审判。成长来自让直觉接受现实检验，同时允许答案逐步显现。",
    3: "你以创造、滋养与连接赋予经验意义。世界与吊人让这种创造力同时带有整合和换位视角：优势是把零散经验组织成有生命的整体；压力下容易过度付出、停滞或用照顾别人回避自身需要。导师课题是保留边界，让牺牲真正服务于成长。",
    4: "你倾向建立秩序、边界和可依靠的结构。死神与愚人同时要求你既能收尾又能重新出发：优势是把变化落实为新框架；压力下可能在控制与冲动之间摆动。真正的权威来自知道何时坚持、何时结束，以及如何为未知保留安全边界。",
    5: "你的成长轴线围绕学习、教导与调和差异。节制使教皇不止遵循传统，也需要通过实践不断配比和修正：优势是理解系统并把复杂知识传递给别人；压力下可能过度依赖权威或追求唯一正确答案。导师课题是让经验、信念与现实彼此校准。",
    6: "你通过关系与选择认识自己，敏锐于他人的期待、吸引力和价值差异。恶魔作为导师把欲望、依附、权力与选择权带到台前：优势是理解人际动力并作出有承诺的选择；压力下可能讨好、纠缠或把决定交给关系。成长不是拒绝欲望，而是看清代价后仍能自主选择。",
    7: "你以方向感、行动和自我掌舵回应世界。高塔作为导师会检验目标所依赖的结构是否真实可靠：优势是危机中迅速整队并推进；压力下可能急于证明或硬撑已经失效的路线。成长来自允许事实拆除虚假确定性，再以更稳固的基础继续前进。",
    8: "你的核心力量来自耐心、勇气和与本能力量合作。星星把力量导向真实、希望与长期愿景：优势是能在压力中保持韧性并鼓舞他人；压力下可能逞强、压抑愤怒或只靠理想支撑。导师课题是让脆弱与力量并存，把愿景落实为持续行动。",
    9: "你以独处、研究和经验整理形成自己的理解。月亮使这条道路伴随想象、梦境与不确定性：优势是深入观察并从复杂经验中提炼智慧；压力下可能封闭、过度怀疑或陷入投射。成长来自为内在世界建立现实出口，以验证和交流保护敏感度。",
}

SUN_MAJOR = {
    "白羊座": 4, "金牛座": 5, "双子座": 6, "巨蟹座": 7, "狮子座": 8, "处女座": 9,
    "天秤座": 11, "天蝎座": 13, "射手座": 14, "摩羯座": 15, "水瓶座": 17, "双鱼座": 18,
}
COURT_CARDS = {
    "白羊座": "权杖皇后", "金牛座": "星币国王", "双子座": "宝剑骑士", "巨蟹座": "圣杯皇后",
    "狮子座": "权杖国王", "处女座": "星币骑士", "天秤座": "宝剑皇后", "天蝎座": "圣杯国王",
    "射手座": "权杖骑士", "摩羯座": "星币皇后", "水瓶座": "宝剑国王", "双鱼座": "圣杯骑士",
}

CARD_SYMBOLS = {
    1: (("举起的权杖", "把意图带入行动"), ("桌上的四元素工具", "资源已经在场"), ("无限符号", "持续流动的专注")),
    2: (("黑白双柱", "在两极之间守住观察"), ("卷轴", "尚未完全展开的知识"), ("石榴帷幕", "内在世界的丰饶与边界")),
    3: (("麦田", "被照料后成熟的现实"), ("石榴长袍", "生命力与创造"), ("流水", "感受持续滋养土地")),
    4: (("石座", "可依靠的结构"), ("白羊头饰", "直接而有担当的行动"), ("远山", "权威背后的长期考验")),
    5: (("两把钥匙", "经验与方法的入口"), ("举起的手势", "传授也意味着责任"), ("两位学习者", "知识在关系中流动")),
    6: (("相望的人物", "选择发生在真实关系里"), ("天使", "更高价值的见证"), ("两棵不同的树", "欲望与意识同时在场")),
    7: (("黑白狮身兽", "相反力量需要协调"), ("星冠", "方向来自清楚的意图"), ("城墙", "离开熟悉秩序去推进")),
    8: (("无限符号", "力量可以柔韧而持续"), ("红色狮子", "欲望与本能力量"), ("轻柔触碰", "关系比压制更能形成合作"), ("花环", "温柔并不等于软弱")),
    9: (("提灯", "只照亮眼前一步"), ("山巅", "经验来自独自攀登"), ("手杖", "在不确定中提供支点")),
    10: (("转轮", "处境持续变化"), ("四角生物", "变化中仍有稳定见证"), ("上升与下降的人物", "位置改变带来不同视角")),
    11: (("天平", "让不同重量接受比较"), ("直立之剑", "决定需要清晰边界"), ("红色帷幕", "判断背后仍有人情与欲望")),
    12: (("倒悬姿态", "主动换一个角度"), ("头部光环", "停顿可能带来理解"), ("被缚的脚", "限制也会暴露选择")),
    13: (("白马", "变化继续向前"), ("黑色旗帜", "结束被明确承认"), ("远处日出", "终点与新阶段相连")),
    14: (("两只杯", "经验在往返中重新配比"), ("一脚水中一脚岸上", "感受与现实同时校准"), ("远方道路", "整合是一段持续试验")),
    15: (("锁链", "束缚也可能有松开的空间"), ("火炬", "本能既能照明也能灼伤"), ("高台人物", "权力关系需要被看见")),
    16: (("闪电", "事实突然照亮裂缝"), ("坠落王冠", "旧权威失去支点"), ("飞落人物", "身体先感到结构改变")),
    17: (("裸露人物", "无需盔甲的真实"), ("双重水流", "内外资源重新循环"), ("八角星", "远方愿景为当下定向")),
    18: (("月亮", "光线柔弱时轮廓会变化"), ("犬与狼", "熟悉本能和野性本能并存"), ("水中甲壳动物", "深层感受缓慢浮现")),
    19: (("孩童", "坦率地享受生命力"), ("向日葵", "注意力朝光亮生长"), ("白马", "活力被温和承载")),
    20: (("号角", "某种召唤要求回应"), ("起身的人群", "旧经验获得新的位置"), ("远山", "复盘通向更广阔视野")),
    21: (("花环", "阶段形成完整边界"), ("舞者", "完成之中仍有流动"), ("四角生物", "多个维度共同见证整合")),
    22: (("悬崖", "未知就在下一步"), ("白玫瑰", "保持开放与单纯意图"), ("小狗", "本能既催促也提醒")),
}

NUMBER_THEMES = {
    1: ("太阳的点与圆形", "完整、不朽、潜能；开端、首创与意志"),
    2: ("带端点的线段与阴阳符号", "平衡、适应、两极、抉择与镜像"),
    3: ("带 A／B／C 三点的平面与三角形", "显化、变动、抱负、成形、协作与边界"),
    4: ("圆规、矩尺与正四面体", "秩序、守护、成就、边界与物质稳定"),
    5: ("五角星与方底金字塔", "颠覆、自由、冒险、变革、欲望与创造"),
    6: ("立方体、复合六芒星与一笔画六芒星", "和谐、爱、责任、平衡与完整"),
    7: ("锐角／钝角七芒星与生命之种", "想象、隐秘、求索、足智多谋、直觉与学识"),
    8: ("拉克希米八角星与月相图", "自律、领导、成就、掌控、成功与权威"),
    9: ("复合九芒星与九宫矩阵", "洞见、疗愈、理想、勇气、悲悯与灵感"),
    10: ("四元数点阵与生命之树", "循环、生死、成熟、收获、完成与更新"),
}

# 同一生命数字进入火、 水、风、土后的逐牌含义；避免用同一句模板重复四次。
OPPORTUNITY_MEANINGS = {
    1: {
        "权杖": "火把潜能点燃成第一步：先允许愿望出现，再为它选定方向。机会在于主动发起；需要留意热情很快，却没有持续投入。",
        "圣杯": "水让开端成为情感的容器：愿意感受、接纳与表达，关系才有新的入口。机会在于敞开心；也要分清真情流动与一时投射。",
        "宝剑": "风把潜能化成一个清楚念头或决定：命名问题、切开混乱、说出立场。机会在于辨明真相；锋利时也别忽略他人的感受。",
        "星币": "土把种子放进可触摸的现实：身体、金钱、技能或工作迎来起点。机会在于稳稳接住资源，并用具体行动让它开始生长。",
    },
    2: {
        "权杖": "火遇见两极，行动前需要辨认真正想走的方向。机会在于规划、比较与扩大视野；别让反复权衡替代了必要的第一步。",
        "圣杯": "水中的二形成相遇与互相回应：情感因平等交换而流动。机会在于建立信任与联盟，同时保留边界，不用迎合换取亲近。",
        "宝剑": "风中的二把人带到暂时僵持处：两种判断都有理由。机会在于安静收集信息、容纳矛盾；也要为决定设下明确期限。",
        "星币": "土中的二要求在变化里保持节奏：资源、时间与责任需要灵活调度。机会在于边做边校准，而不是追求永远不变的完美平衡。",
    },
    3: {
        "权杖": "火中的三让意图越过起点，开始眺望更远的可能。机会在于拓展、等待回应并修正路线；成果尚在途中，不必过早下结论。",
        "圣杯": "水中的三把情感显化为分享、庆祝与支持网络。机会在于让喜悦被共同见证；同时留意热闹是否遮住了真正需要被听见的感受。",
        "宝剑": "风中的三使分离、失望或刺痛变得无法回避。机会在于诚实命名伤口、看清事实；理解痛苦不等于让它永久定义自己。",
        "星币": "土中的三把能力带进合作与制作：不同专长要在同一结构里配合。机会在于接受反馈、打磨手艺，并让贡献获得清楚评价。",
    },
    4: {
        "权杖": "火中的四把行动安放进稳定空间，适合庆祝阶段完成、建立归属。机会在于巩固支持系统；别把暂时安稳误当成永不变化。",
        "圣杯": "水中的四把感受收回内部，熟悉选项可能暂时失去吸引力。机会在于辨认真正渴望；也要留意冷淡是否只是疲惫或防御。",
        "宝剑": "风中的四让思考暂停，恢复本身就是必要工作。机会在于退后、休息、整合信息；安静不是逃避，前提是之后愿意重新回应。",
        "星币": "土中的四重视保存、边界与掌控资源。机会在于稳住基础、明确所有权；若抓得太紧，安全感也可能变成不流动的防御。",
    },
    5: {
        "权杖": "火中的五让不同意志正面碰撞，竞争也能暴露真实能力。机会在于练习协商与应变；别为了证明自己，把差异升级为消耗。",
        "圣杯": "水中的五让注意力停在失去与遗憾上。机会在于认真哀悼，同时回头看见仍被保留的关系和资源，让情感重新开始流动。",
        "宝剑": "风中的五提醒胜负可能附带关系代价。机会在于辨认冲突中的权力、语言与底线；赢下一次争辩，不一定赢得真正需要的结果。",
        "星币": "土中的五呈现匮乏、孤立或身体压力。机会在于承认需要并寻找实际援助；困难并不证明个人失败，支持往往比想象中更靠近。",
    },
    6: {
        "权杖": "火中的六让努力被看见，带来认可、信心与带领他人的机会。接受肯定时，也要记得成绩来自过程与协作，而非永久身份。",
        "圣杯": "水中的六让记忆、纯真与旧关系回到眼前。机会在于取回温柔资源、修复连接；同时分辨怀旧是真滋养，还是逃离当下。",
        "宝剑": "风中的六意味着带着经验渡向较平静的水域。机会在于转换环境与叙事；尚未解决的情绪可以同行，但不必继续掌舵。",
        "星币": "土中的六关注资源如何给予、接受与分配。机会在于建立公平互助；需要看见谁掌握决定权，以及帮助是否真正尊重对方需要。",
    },
    7: {
        "权杖": "火中的七要求守住已经选择的位置。机会在于面对压力时明确立场、调动勇气；防卫若成为惯性，也会让所有交流都像挑战。",
        "圣杯": "水中的七让想象与欲望同时涌现，选择因此显得迷人又混乱。机会在于辨认真实需要，用现实标准筛去投射和诱惑。",
        "宝剑": "风中的七强调策略、隐私与非正面路径。机会在于聪明调整方法；同时检查隐瞒、回避或自我欺骗是否正在制造更高代价。",
        "星币": "土中的七让人停下来评估长期投入与收成。机会在于耐心复盘、调整资源；等待应当伴随观察，而不是无限拖延或机械坚持。",
    },
    8: {
        "权杖": "火中的八让能量迅速汇聚，消息、行动或进度一齐加快。机会在于顺势推进并保持方向；速度很快时，更要确认目标仍然正确。",
        "圣杯": "水中的八要求离开已无法滋养内心的情境，去寻找更深价值。机会在于诚实告别；离开不是否定过去，而是承认需求已经改变。",
        "宝剑": "风中的八呈现被念头、规则或恐惧围住的感受。机会在于检验限制是否全部真实，从一个可控动作开始，逐步取回选择权。",
        "星币": "土中的八把力量放进重复练习、工艺与细节。机会在于用纪律累积熟练度；也要定期抬头，确认勤奋正在服务真正想建造的事。",
    },
    9: {
        "权杖": "火中的九带着旧伤继续守卫成果，显示韧性也显示疲惫。机会在于调整边界、保存体力；坚持不等于永远独自硬撑。",
        "圣杯": "水中的九邀请人承认愿望、享受已拥有的满足。机会在于接纳快乐并表达感谢；同时辨认舒适是否掩盖了更深的情感需要。",
        "宝剑": "风中的九让焦虑、内疚或反复思虑在夜里放大。机会在于把念头写下并寻求支持，用事实区分真实责任与想象中的灾难。",
        "星币": "土中的九呈现独立、品味与长期劳动的成果。机会在于享用自己建立的生活；自主并不排斥亲密，也不必用成就证明价值。",
    },
    10: {
        "权杖": "火中的十把使命累积成沉重负担。机会在于完成、分工并重新排序责任；能承担很多并不表示每件事都必须由自己扛住。",
        "圣杯": "水中的十让情感归属扩展为家庭、群体与共享愿景。机会在于共同创造幸福；别用理想画面压住关系里真实而复杂的声音。",
        "宝剑": "风中的十把某个叙事推到终点，旧方式已无法继续。机会在于承认结束、停止重复伤害；最低点也让新的视角开始出现。",
        "星币": "土中的十关乎传承、家族、长期资产与稳定结构。机会在于把成果延续给更大系统；也要检查传统是否仍适合当下的人。",
    },
}

DECAN_RULERS = {
    ("权杖", 2): "火星", ("权杖", 3): "太阳", ("权杖", 4): "金星", ("星币", 5): "水星", ("星币", 6): "月亮", ("星币", 7): "土星",
    ("宝剑", 8): "木星", ("宝剑", 9): "火星", ("宝剑", 10): "太阳", ("圣杯", 2): "金星", ("圣杯", 3): "水星", ("圣杯", 4): "月亮",
    ("权杖", 5): "土星", ("权杖", 6): "木星", ("权杖", 7): "火星", ("星币", 8): "太阳", ("星币", 9): "金星", ("星币", 10): "水星",
    ("宝剑", 2): "月亮", ("宝剑", 3): "土星", ("宝剑", 4): "木星", ("圣杯", 5): "火星", ("圣杯", 6): "太阳", ("圣杯", 7): "金星",
    ("权杖", 8): "水星", ("权杖", 9): "月亮", ("权杖", 10): "土星", ("星币", 2): "木星", ("星币", 3): "火星", ("星币", 4): "太阳",
    ("宝剑", 5): "金星", ("宝剑", 6): "水星", ("宝剑", 7): "月亮", ("圣杯", 8): "土星", ("圣杯", 9): "木星", ("圣杯", 10): "火星",
}

SIGN_START = {"白羊座": 0, "金牛座": 30, "双子座": 60, "巨蟹座": 90, "狮子座": 120, "处女座": 150, "天秤座": 180, "天蝎座": 210, "射手座": 240, "摩羯座": 270, "水瓶座": 300, "双鱼座": 330}
PLANET_SYMBOL = {"太阳":"☉", "月亮":"☽", "水星":"☿", "金星":"♀", "火星":"♂", "木星":"♃", "土星":"♄"}
SIGN_SYMBOL = {"白羊座":"♈", "金牛座":"♉", "双子座":"♊", "巨蟹座":"♋", "狮子座":"♌", "处女座":"♍", "天秤座":"♎", "天蝎座":"♏", "射手座":"♐", "摩羯座":"♑", "水瓶座":"♒", "双鱼座":"♓"}
SIGN_EMOJI_CODE = {"白羊座":"2648", "金牛座":"2649", "双子座":"264a", "巨蟹座":"264b", "狮子座":"264c", "处女座":"264d", "天秤座":"264e", "天蝎座":"264f", "射手座":"2650", "摩羯座":"2651", "水瓶座":"2652", "双鱼座":"2653"}

# RWS court names mapped from Golden Dawn zodiacal court ranges.  Start/end are
# absolute tropical longitude and wrap at 360 degrees.
COURT_RANGES = (
    (350, 20, "权杖皇后", "火中之水"), (20, 50, "星币骑士", "土中之风"), (50, 80, "宝剑国王", "风中之火"),
    (80, 110, "圣杯皇后", "水中之水"), (110, 140, "权杖骑士", "火中之风"), (140, 170, "星币国王", "土中之火"),
    (170, 200, "宝剑皇后", "风中之水"), (200, 230, "圣杯骑士", "水中之风"), (230, 260, "权杖国王", "火中之火"),
    (260, 290, "星币皇后", "土中之水"), (290, 320, "宝剑骑士", "风中之风"), (320, 350, "圣杯国王", "水中之火"),
)

SABIAN_SYMBOLS = {
    # The one exact Chinese entry present in the supplied optimization brief.
    282: "图文并茂的自然科学讲座揭示生命的未知面向。",
}

# (start MMDD, end MMDD, sign, suit label, rank), following the photographed ten-day table.
DECANS = (
    (321, 330, "白羊座", "权杖", 2), (331, 410, "白羊座", "权杖", 3), (411, 420, "白羊座", "权杖", 4),
    (421, 430, "金牛座", "星币", 5), (501, 510, "金牛座", "星币", 6), (511, 520, "金牛座", "星币", 7),
    (521, 531, "双子座", "宝剑", 8), (601, 610, "双子座", "宝剑", 9), (611, 620, "双子座", "宝剑", 10),
    (621, 701, "巨蟹座", "圣杯", 2), (702, 711, "巨蟹座", "圣杯", 3), (712, 721, "巨蟹座", "圣杯", 4),
    (722, 801, "狮子座", "权杖", 5), (802, 811, "狮子座", "权杖", 6), (812, 822, "狮子座", "权杖", 7),
    (823, 901, "处女座", "星币", 8), (902, 911, "处女座", "星币", 9), (912, 922, "处女座", "星币", 10),
    (923, 1002, "天秤座", "宝剑", 2), (1003, 1012, "天秤座", "宝剑", 3), (1013, 1022, "天秤座", "宝剑", 4),
    (1023, 1101, "天蝎座", "圣杯", 5), (1102, 1112, "天蝎座", "圣杯", 6), (1113, 1122, "天蝎座", "圣杯", 7),
    (1123, 1202, "射手座", "权杖", 8), (1203, 1212, "射手座", "权杖", 9), (1213, 1221, "射手座", "权杖", 10),
    (1222, 1230, "摩羯座", "星币", 2), (1231, 109, "摩羯座", "星币", 3), (110, 119, "摩羯座", "星币", 4),
    (120, 129, "水瓶座", "宝剑", 5), (130, 208, "水瓶座", "宝剑", 6), (209, 218, "水瓶座", "宝剑", 7),
    (219, 229, "双鱼座", "圣杯", 8), (301, 310, "双鱼座", "圣杯", 9), (311, 320, "双鱼座", "圣杯", 10),
)
SUITS = (("wands", "权杖"), ("cups", "圣杯"), ("swords", "宝剑"), ("pents", "星币"))
SUIT_CODES = {label: code for code, label in SUITS}
ASSET_DIR = Path(__file__).resolve().parent.parent / "assets" / "rws"
ASSET_ROOT = ASSET_DIR.parent
NUMBER_IMAGE_DIR = ASSET_ROOT / "number photo"
ASTROLOGY_CHART = ASSET_ROOT / "tarot astrology" / "taro astrology.png"
EMOJI_DIR = ASSET_ROOT / "emoji"

ROLE_DEFINITIONS = {
    "性格牌": "你较容易让别人看见的处世方式，也是人生会反复布置给你的主要功课；它不是性格标签，而是你最常用、也最值得精炼的一套能力。",
    "灵魂牌": "比外在表现更安静、持久的内在动力，说明什么会让你感到真正有意义；当生活很嘈杂时，它像心里的指南针。",
    "隐藏／导师牌": "起初可能陌生、抗拒或不容易认领，却会在成长中成为老师的部分；它常从阴影里递来一件你尚未熟练的工具。",
    "太阳星座牌": "太阳星座借用的大阿尔克纳语言，描述你如何发光、表达意志并建立自我认同；它补充出生牌，而不取代出生牌。",
    "性格／灵魂牌组": "这组特殊出生牌共同承担外在学习与内在动力，需要按一条连续的成长线阅读。",
}

NUMBER_FULL = {
    1: (("合一", "完整、不朽、潜能"), ("行动", "开端、孕育、首创"), ("自我", "自信果断、独立、创造力、意志")),
    2: (("平衡", "平衡均衡、适应变通"), ("对立", "两极对立、电性正负、抉择取舍、人生岔路、境遇考验"), ("他人", "洞察觉知、镜像映照、情爱浪漫、注视凝视、自我觉察")),
    3: (("新生", "显化、变动、抱负"), ("成形", "掌控、实现、边界"), ("社群", "群体、协作、友谊、约束")),
    4: (("秩序", "家庭、规训、居所、守护"), ("成就", "事业、财富、声望"), ("稳定", "边界、物质元素、沉静、大地、稳固")),
    5: (("颠覆", "脱离物质循环束缚、灵性、冒险、变革、失衡"), ("创造", "远行、欲望、情欲、能量、吸引力")),
    6: (("和谐", "美好、爱、安宁顺遂"), ("使命", "繁衍、牺牲、责任"), ("完整", "平衡、圆满、阴阳和合")),
    7: (("神秘", "想象、隐秘、魅惑、力量、生机"), ("英雄", "探索求索、自我、足智多谋、热忱"), ("技艺", "智慧、直觉、学识")),
    8: (("统御", "自律、领导力、成就"), ("理性", "掌控力、成功、权威")),
    9: (("魔法", "通灵能力、洞见、疗愈"), ("力量", "理想主义、勇气、独立"), ("灵性", "悲悯、慷慨、灵感")),
    10: (("更新", "循环、生与死、生机、过度成熟、收获、完成"),),
}

MINOR_TITLES = {
    1: {"权杖":"火之力的根源", "圣杯":"水之力的根源", "宝剑":"风之力的根源", "星币":"土之力的根源"},
    2: {"权杖":"支配", "圣杯":"情爱", "宝剑":"和平", "星币":"变化"},
    3: {"权杖":"美德", "圣杯":"丰饶", "宝剑":"悲伤", "星币":"工作"},
    4: {"权杖":"成就", "圣杯":"安逸", "宝剑":"休战", "星币":"权力"},
    5: {"权杖":"纷争", "圣杯":"失望", "宝剑":"失败", "星币":"忧虑"},
    6: {"权杖":"胜利", "圣杯":"欢愉", "宝剑":"学识", "星币":"成功"},
    7: {"权杖":"英勇", "圣杯":"幻灭", "宝剑":"徒劳", "星币":"失败"},
    8: {"权杖":"迅速", "圣杯":"怠惰", "宝剑":"阻滞", "星币":"审慎"},
    9: {"权杖":"力量", "圣杯":"幸福", "宝剑":"残酷", "星币":"收益"},
    10:{"权杖":"压迫", "圣杯":"满足", "宝剑":"毁灭", "星币":"财富"},
}

MINOR_KEYWORDS = {
    "权杖": {1:"开端・意志・点燃",2:"规划・主导・远见",3:"拓展・等待・远方",4:"庆祝・归属・稳定",5:"竞争・碰撞・磨合",6:"胜利・认可・带领",7:"立场・防守・勇气",8:"迅速・消息・推进",9:"韧性・边界・坚持",10:"责任・重担・完成"},
    "圣杯": {1:"感受・接纳・新生",2:"相遇・互惠・连接",3:"分享・庆祝・支持",4:"停顿・倦怠・辨愿",5:"失落・哀悼・余留",6:"记忆・温柔・回归",7:"想象・诱惑・选择",8:"离开・倦怠・寻找",9:"满足・愿望・享受",10:"归属・共享・圆满"},
    "宝剑": {1:"真相・决定・清晰",2:"僵持・权衡・期限",3:"伤痛・事实・疗愈",4:"休息・恢复・整合",5:"冲突・代价・底线",6:"过渡・迁移・释重",7:"策略・隐私・检验",8:"限制・困局・视角",9:"焦虑・思虑・求助",10:"终结・触底・新叙事"},
    "星币": {1:"资源・身体・扎根",2:"调度・变化・节奏",3:"协作・手艺・建造",4:"保存・边界・掌控",5:"匮乏・援助・现实",6:"给予・接受・公平",7:"等待・评估・长期",8:"勤练・技艺・专注",9:"独立・成果・品味",10:"传承・家族・稳定"},
}

ROLE_EMOJI = {
    "性格牌": "🦁", "灵魂牌": "💗", "隐藏／导师牌": "🌑", "太阳星座牌": "☀️",
    "命运牌": "🎯", "潜力牌": "👑", "月亮形象牌": "🌙", "上升形象牌": "🌅",
}
SUIT_EMOJI = {"权杖": "🔥", "圣杯": "🏆", "宝剑": "🗡️", "星币": "🪙"}
AGE_BANDS = (
    (0, 9, "🌱"), (10, 19, "🎒"), (20, 29, "🌿"), (30, 39, "🧭"),
    (40, 49, "🌳"), (50, 59, "🔥"), (60, 69, "🌾"), (70, 79, "🌙"),
    (80, 89, "✨"), (90, 100, "🌌"),
)

PHASES = [
    (0, 5, "幼年：回看安全感、依恋、身体发展与表达环境，不把成人责任归给当时的孩子"),
    (6, 11, "小学年龄段：关注学习习惯、同伴关系和自信建立，避免把成绩等同于自我价值"),
    (12, 14, "青春早期：身份感、同伴影响与身体变化加速，练习边界、休息和情绪命名"),
    (15, 17, "高中年龄段：在学业、友谊和自我选择间排序，不用一次结果定义未来"),
    (18, 21, "成年初期：练习独立生活、学习探索与关系选择，把试错转为可复用经验"),
    (22, 34, "成年早期：同步建设能力、职业、财务和关系边界，不必服从单一人生时间表"),
    (35, 44, "成年中段：重新分配事业、家庭、领导责任与健康投入，避免长期透支"),
    (45, 59, "中年阶段：更新优先级，关注身体变化、资产安排、照护责任与意义感"),
    (60, 74, "成熟晚年：在健康、家庭角色、社会连接与个人兴趣之间建立新节奏"),
    (75, 89, "高龄阶段：优先维护自主、尊严、身体舒适与社会连接，沟通照护安排"),
    (90, 10000, "长寿阶段：以舒适、安全、陪伴与生命回顾为先，让重要安排清晰简化"),
]

NODE_RE = re.compile(r"^(\d{4}(?:-\d{2}-\d{2})?)=(.+)$")

WELCOME_MARKDOWN = """**Hi，欢迎来到塔罗的象征世界 ✨**

在翻开属于你的个人塔罗图谱之前，让我们先从“TARO”这个名字开始。

TARO 的四个字母可以不断转动、重新排列，形成 **ROTA、TORA、ORAT、ATOR**。在西方神秘学传统中，它们常被连缀成一句富有谜语色彩的箴言：

**ROTA TARO ORAT TORA ATOR**

它可以被象征性地理解为：**塔罗之轮转动，并向我们诉说生命的法则。**

这句话并不要求我们寻找一个唯一、标准的答案。它更像是在提醒我们：塔罗不是一套静止的定义，而是一种会随着人生经历不断展开的象征语言。同一张牌，在不同年龄、关系与处境中，可能向我们展示完全不同的侧面。我们不是来接受某种注定的命运，而是借助这些古老图像，更细致地观察自己正在经历什么、如何作出选择，以及想要成为怎样的人。

巴斯克裔文化人类学家、作家与塔罗研究者 **安吉莉丝·艾伦（Angeles Arrien）**，曾介绍过一种根据出生日期寻找个人大阿尔克纳牌的方法。这样的个人牌在某种程度上类似于占星学中的太阳星座：它并不能概括一个人的全部，却可以成为我们与塔罗原型建立长期关系的起点。

当一张牌通过出生日期与我们相遇，它并不是在替我们规定性格或预告未来，而是在提供一组可以反复探索的问题：我惯常如何面对世界？什么力量长期推动着我？我需要学习、接纳或重新理解的生命主题是什么？

除了大阿尔克纳所代表的生命原型，小阿尔克纳中也蕴藏着丰富的数字、元素、星座、人格与现实经验。它们将宏大的象征带回日常生活，让我们看见自己如何行动、感受、思考，并与现实世界建立关系。

而这一次，我们就从一个与你相伴已久的个人坐标——**生日**——开始。让数字与牌面彼此映照，轻轻推开这扇通往塔罗世界的门。接下来的内容不是关于“你注定是谁”的判词，而是一张邀请你持续观察、书写与验证的个人象征地图。🌙

**现在，让我们看看，哪些牌正在等待与你相遇。**"""

REPORT_SIGNATURE_NAME = "liyomm"
REPORT_SIGNATURE_WECHAT = "LittleYellow_bu"
REPORT_SIGNATURE = f"本skill由 {REPORT_SIGNATURE_NAME} 制作｜wechat：{REPORT_SIGNATURE_WECHAT}"


def parse_date(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("日期必须使用 YYYY-MM-DD 格式") from exc


def reduce_card(total: int) -> int:
    value = sum(int(ch) for ch in str(total))
    while value > 22:
        value = sum(int(ch) for ch in str(value))
    return value


def digit_expression(value: int) -> str:
    return " + ".join(str(ch) for ch in str(value))


def reduction_text(value: int) -> str:
    parts = []
    cursor = value
    while True:
        reduced = sum(int(ch) for ch in str(cursor))
        parts.append(f"{digit_expression(cursor)} = {reduced}")
        if reduced <= 22:
            return " → ".join(parts)
        cursor = reduced


def birth_profile(birth: dt.date) -> dict[str, object]:
    total = birth.month + birth.day + birth.year
    personality = reduce_card(total)
    chain = [personality]
    cursor = personality
    while cursor > 9:
        cursor = sum(int(ch) for ch in str(cursor))
        chain.append(cursor)
    soul = cursor
    constellation = tuple(value for value in (soul, soul + 9, soul + 18) if value <= 22)
    structure = "standard"
    core_group = (personality, soul) if personality != soul else (personality,)
    if personality == 19:
        structure, core_group, hidden = "19-10-1", (19, 10, 1), ()
    elif personality == 22:
        structure, core_group, hidden = "22-0-4", (22, 4), ()
    elif 14 <= personality <= 18:
        structure, hidden = "night", ()
    else:
        hidden = tuple(value for value in constellation if value not in {personality, soul})
    return {
        "total": total, "personality": personality, "soul": soul, "chain": tuple(chain),
        "hidden": hidden, "minor_ranks": (1, 10) if soul == 1 else (soul,),
        "constellation": CONSTELLATIONS[soul], "structure": structure, "core_group": core_group,
    }


def sabian_lookup(abs_longitude: float) -> str | None:
    """Return the single supplied Chinese Sabian symbol for a tropical degree."""
    path = Path(__file__).resolve().parent.parent / "references" / "sabian-symbols.md"
    if not path.exists():
        return SABIAN_SYMBOLS.get(int(abs_longitude) + 1)
    sign_alias = {name.removesuffix("座"): start for name, start in SIGN_START.items()}
    pattern = re.compile(r"(白羊|金牛|双子|巨蟹|狮子|处女|天秤|天蝎|射手|摩羯|水瓶|双鱼)\s*(\d+)\s*[°度]?\s*[–—-]\s*(\d+)\s*度：([^<\r\n|]+)")
    target = int(abs_longitude) + 1
    for sign, low, _high, symbol in pattern.findall(path.read_text(encoding="utf-8")):
        key = sign_alias[sign] + int(low) + 1
        if key == target:
            return symbol.strip()
    return SABIAN_SYMBOLS.get(target)


def solar_symbols(birth: dt.date) -> dict[str, object]:
    key = birth.month * 100 + birth.day
    for start, end, sign, suit, rank in DECANS:
        inside = start <= key <= end if start <= end else key >= start or key <= end
        if inside:
            sign_entries = [entry for entry in DECANS if entry[2] == sign]
            sign_start = sign_entries[0][0]
            ref_year = 2000
            def ref_date(mmdd: int) -> dt.date:
                month, day = divmod(mmdd, 100)
                return dt.date(ref_year if month >= 3 else ref_year + 1, month, day)
            birth_ref = dt.date(ref_year if birth.month >= 3 else ref_year + 1, birth.month, birth.day)
            start_ref = ref_date(sign_start)
            degree = max(0.0, min(29.999, float((birth_ref - start_ref).days)))
            abs_longitude = (SIGN_START[sign] + degree + 0.5) % 360
            ruler = DECAN_RULERS[(suit, rank)]
            court_name = COURT_CARDS[sign]
            court_element = court_element_for_card(court_name)
            sabian_degree = int(abs_longitude) + 1
            return {
                "sign": sign,
                "major": SUN_MAJOR[sign],
                "destiny": f"{suit}{rank}",
                "decan": 1 + sign_entries.index((start, end, sign, suit, rank)),
                "ruler": ruler,
                "degree": degree,
                "degree_interval": f"{int(degree)}°～{int(degree)+1}°",
                "longitude": abs_longitude,
                "sabian_degree": sabian_degree,
                "sabian": sabian_lookup(abs_longitude),
                "court": court_name,
                "court_element": court_element,
            }
    raise ValueError(f"无法识别生日区间：{birth.month}-{birth.day}")


def court_for_longitude(longitude: float) -> tuple[str, str]:
    value = longitude % 360
    for start, end, name, element in COURT_RANGES:
        if (start <= value < end) if start < end else (value >= start or value < end):
            return name, element
    raise ValueError(f"无法匹配宫廷牌黄道区间：{longitude}")


def court_element_for_card(card: str) -> str:
    for _, _, name, element in COURT_RANGES:
        if name == card:
            return element
    raise ValueError(f"无法匹配宫廷牌元素：{card}")


def longitude_label(longitude: float) -> str:
    value = longitude % 360
    starts = sorted((start, sign) for sign, start in SIGN_START.items())
    start, sign = max((item for item in starts if item[0] <= value), default=starts[-1])
    return f"{sign} {value - start:.2f}°"


def image_positions(args: argparse.Namespace, solar: dict[str, object]) -> list[dict[str, str]]:
    positions = [{"role": "太阳形象牌｜我想成为怎样的人", "source": "太阳", "sign": str(solar["sign"]), "basis": "星座层级对应", "card": str(solar["court"]), "element": str(solar["court_element"])}]
    for role, source, longitude, sign in (
        ("月亮形象牌｜独处时的我", "月亮", getattr(args, "moon_longitude", None), getattr(args, "moon_sign", "")),
        ("上升形象牌｜我如何走进一个房间", "上升", getattr(args, "rising_longitude", None), getattr(args, "rising_sign", "")),
    ):
        resolved_sign = sign or (longitude_label(longitude).split()[0] if longitude is not None else "")
        if resolved_sign:
            card = COURT_CARDS[resolved_sign]
            position = {"role": role, "source": source, "sign": resolved_sign, "basis": "Mary 星座—宫廷牌对应", "card": card, "element": court_element_for_card(card)}
            if longitude is not None:
                position["longitude"] = f"{longitude % 360:.3f}"
            positions.append(position)
    return positions


def position_label(position: dict[str, str]) -> str:
    if "longitude" in position:
        return f"黄道位置：{longitude_label(float(position['longitude']))}（绝对黄经 {float(position['longitude']):.3f}°；形象牌依 {position['basis']}）"
    return f"星座：{position['sign']}（{position['basis']}）"


def court_portrait(position: dict[str, str]) -> str:
    card, element, source = position["card"], position["element"], position["source"]
    suit = next(name for name in ("权杖", "圣杯", "宝剑", "星币") if name in card)
    movement = {"权杖": "先点燃行动与热情", "圣杯": "先感受气氛与关系", "宝剑": "先辨认信息与边界", "星币": "先照看身体与现实条件"}[suit]
    entrance = {"太阳":"这是你想主动呈现、也愿意慢慢长成的样子", "月亮":"这是独处或足够安全时更自然流露的样子", "上升":"这是别人初见你时最先接收到的气场"}[source]
    return f"{card}像一位一进房间就会{movement}的人：先用最熟悉的方式摸清现场，再决定怎么靠近。{entrance}。{element}让它既有魅力也有小脾气——顺畅时可靠又有回应，失衡时则可能只听见自己最熟悉的频道。成熟不是换掉这位人物，而是让TA学会看见别人也在房间里。"


def card_role_text(card_roles: list[str]) -> str:
    definitions = {
        "性格牌": "较容易表现出来的人生课题，以及面对世界的惯常方式",
        "灵魂牌": "更内在、更持久的生命动力与深层学习主题",
        "隐藏／导师牌": "暂时不容易认同，却可能逐渐成为资源的部分",
        "太阳星座牌": "太阳表达自我认同与生命力时采用的象征语言",
        "性格／灵魂牌组": "共同参与外在学习与内在动力的特殊出生牌组",
    }
    return "；".join(f"{role}：{definitions[role]}" for role in card_roles)


def destiny_symbol_text(destiny: str) -> str:
    if destiny == "星币3":
        return "**教堂／工坊的拱顶**：工作发生在共同结构中；**三位人物**：知识、委托与手艺需要沟通；**手中的图纸**：愿景要能被说明；**三枚星币**：成果在合作中获得形状"
    suit = destiny[:2]; rank = destiny[2:]
    suit_detail = {"权杖":"木杖与人物的动作", "圣杯":"金色杯器与水的距离", "宝剑":"剑刃的方向与天空", "星币":"星币图案与现实场景"}[suit]
    return f"**{rank} 个{ suit }符号**：数字被放进具体画面；**{suit_detail}**：元素通过可见物件说话；**前景与远景**：当下行动与更长过程彼此参照"


def symbol_emoji(name: str) -> str:
    for word, icon in (("狮","🦁"),("心","💗"),("月","🌙"),("太阳","☀️"),("花","🌺"),("水","💧"),("山","⛰️"),("剑","🗡️"),("星","✨"),("马","🐎"),("王冠","👑"),("人物","🧍"),("手","🤲"),("树","🌳"),("路","🛤️"),("门","🚪"),("旗","🏴"),("闪电","⚡"),("杯","🏆"),("钥匙","🔑"),("卷轴","📜"),("天平","⚖️"),("轮","☸️"),("链","⛓️")):
        if word in name:
            return icon
    return "🔎"


def interpretation_points(number: int, roles: list[str]) -> list[tuple[str, str, str]]:
    joined = "与".join(roles)
    first_symbol = CARD_SYMBOLS[number][0][0]
    return [
        ("🌱", "主要功课", f"{CARDS[number][2]}。放在{joined}的位置，这不是一次通关任务，而是会换着场景回来敲门的练习。"),
        ("✨", "自然优势", f"你较容易调动“{SHORT[number][0]}”这股力量；当牌面的{first_symbol}最先吸引你时，往往也提示当前可用的资源。"),
        ("⚠️", "容易卡住", f"{CARDS[number][3]}。牌不是在挑错，更像轻轻敲桌子：这项能力可能用得太满了。"),
        ("🧭", "给你的提醒", "先做一个身体能承受、现实可验证的小动作；真正稳定的改变，通常没有戏剧配乐，却会在日常里留下脚印。"),
    ]


def opportunity_meta(label: str) -> tuple[str, int, str, str]:
    suit = next(s for s in SUIT_EMOJI if s in label)
    rank = 1 if "王牌" in label else int(re.search(r"(\d+)$", label).group(1))
    return suit, rank, MINOR_TITLES[rank][suit], MINOR_KEYWORDS[suit][rank]


def bold_selected_cards(text: str, names: list[str], pdf: bool = False) -> str:
    """Emphasize only names known to be card references in the current sentence."""
    for name in sorted(set(names), key=len, reverse=True):
        marker = f"<b>{name}</b>" if pdf else f"**{name}**"
        if marker not in text:
            text = text.replace(name, marker)
    return text


def formatted_combination(soul: int, pdf: bool = False) -> str:
    direct_refs = {
        1: ["太阳", "命运之轮"], 2: ["正义", "审判"], 3: ["世界", "吊人"],
        4: ["死神", "愚人"], 5: ["节制", "教皇"], 6: ["恶魔"],
        7: ["高塔"], 8: ["星星"], 9: ["月亮"],
    }
    text = COMBINATION_ANALYSES[soul]
    if soul == 8:
        star = "<b>星星</b>" if pdf else "**星星**"
        strength = "<b>力量</b>" if pdf else "**力量**"
        return text.replace("星星把力量导向", f"{star}把{strength}导向")
    return bold_selected_cards(text, direct_refs[soul], pdf=pdf)


def court_asset_name(card: str) -> str:
    suit_code = {"权杖":"wands", "圣杯":"cups", "宝剑":"swords", "星币":"pents"}[card[:2]]
    rank_code = {"骑士":"knight", "皇后":"queen", "国王":"king"}[card[2:]]
    return f"court_{suit_code}_{rank_code}.jpg"


def make_astrology_highlight(solar: dict[str, object], out_path: Path) -> None:
    from PIL import Image as PILImage, ImageDraw
    source = PILImage.open(ASTROLOGY_CHART).convert("RGBA")
    canvas = PILImage.new("RGBA", source.size, (255, 253, 248, 255))
    overlay = PILImage.new("RGBA", source.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    longitude = float(solar["longitude"])
    decan_start = SIGN_START[str(solar["sign"])] + (int(solar["decan"])-1)*10
    start_angle, end_angle = 180-(decan_start+10), 180-decan_start
    pad = max(8, source.width//100)
    draw.pieslice((pad,pad,source.width-pad,source.height-pad), start=start_angle, end=end_angle, fill=(224,174,55,115))
    canvas = PILImage.alpha_composite(canvas, overlay)
    canvas = PILImage.alpha_composite(canvas, source)
    marker = ImageDraw.Draw(canvas)
    import math
    a = math.radians(180-longitude); cx, cy = source.width/2, source.height/2; radius = source.width*.29
    x, y = cx+radius*math.cos(a), cy+radius*math.sin(a)
    r = max(6, source.width//70)
    marker.ellipse((x-r,y-r,x+r,y+r), fill=(167,46,42,255), outline=(255,253,248,255), width=2)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path, quality=94)


def make_card_cloud(profile: dict[str, object], solar: dict[str, object], current_card: int, out_dir: Path) -> Path:
    from PIL import Image as PILImage, ImageDraw, ImageFont
    import math
    font_path = ASSET_ROOT / "fonts" / "NotoSerifSC-Bold.ttf"
    regular_path = ASSET_ROOT / "fonts" / "NotoSerifSC-Regular.ttf"
    title_font=ImageFont.truetype(str(font_path),30); small_font=ImageFont.truetype(str(regular_path),18)
    canvas=PILImage.new("RGB",(1400,820),"#FBF7EE"); draw=ImageDraw.Draw(canvas)
    personality=int(profile["personality"]); soul=int(profile["soul"])
    is_three_card_group = profile["structure"] == "19-10-1"
    draw.rounded_rectangle((28,28,1372,792),radius=34,fill="#FFFDF8",outline="#B38A45",width=3)
    draw.text((70,60),"我的塔罗关系词云",font=title_font,fill="#2D2139")
    draw.text((70,105),"牌名的大小就是它在这张地图里的音量",font=small_font,fill="#75627F")

    def font(size: int, bold: bool=True):
        return ImageFont.truetype(str(font_path if bold else regular_path),size)

    def label(x: int,y: int,role: str,name: str,keywords: str,size: int,color: str) -> None:
        role_f=font(max(16,size//3),False); name_f=font(size); key_f=font(max(16,size//3),False)
        draw.text((x,y-size*.72),role,font=role_f,fill="#75627F",anchor="mm")
        draw.text((x,y),name,font=name_f,fill=color,anchor="mm")
        draw.text((x,y+size*.72),keywords,font=key_f,fill="#75627F",anchor="mm")

    def star(x: int,y: int,r: int,color: str="#B38A45") -> None:
        pts=[]
        for i in range(16):
            a=-math.pi/2+i*math.pi/8; rr=r if i%2==0 else r*.35
            pts.append((x+math.cos(a)*rr,y+math.sin(a)*rr))
        draw.line(pts+[pts[0]],fill=color,width=3,joint="curve")

    def sun(x: int,y: int,r: int) -> None:
        draw.ellipse((x-r,y-r,x+r,y+r),outline="#B38A45",width=3)
        for i in range(12):
            a=i*math.pi/6; draw.line((x+math.cos(a)*(r+8),y+math.sin(a)*(r+8),x+math.cos(a)*(r+22),y+math.sin(a)*(r+22)),fill="#B38A45",width=3)

    def crescent(x: int,y: int,r: int) -> None:
        draw.arc((x-r,y-r,x+r,y+r),70,290,fill="#75627F",width=4); draw.arc((x-r*.35,y-r,x+r*1.25,y+r),105,255,fill="#75627F",width=3)

    def heart(x: int,y: int,s: int) -> None:
        pts=[]
        for i in range(101):
            t=2*math.pi*i/100
            px=x+s*math.sin(t)**3
            py=y-s*(13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t))/16
            pts.append((px,py))
        draw.line(pts,fill="#A56D77",width=4,joint="curve")

    def compass(x: int,y: int,r: int) -> None:
        draw.ellipse((x-r,y-r,x+r,y+r),outline="#956C2C",width=3); draw.line((x,y-r-10,x,y+r+10),fill="#956C2C",width=2); draw.line((x-r-10,y,x+r+10,y),fill="#956C2C",width=2); star(x,y,int(r*.45))

    # Fine constellation lines link roles without turning the page into a flowchart.
    center=(700,405)
    endpoints=[(700,190),(1035,300),(270,565),(1080,575),(700,675)]
    if soul!=personality: endpoints.append((330,265))
    if profile["hidden"] or is_three_card_group: endpoints.append((330,430))
    for end in endpoints:
        draw.line((center[0],center[1],end[0],end[1]),fill="#E1CFAB",width=2)
        draw.ellipse((end[0]-4,end[1]-4,end[0]+4,end[1]+4),fill="#B38A45")

    central_role = "性格／灵魂牌组｜共同主轴" if is_three_card_group else ("性格牌 × 灵魂牌｜整张地图的主语" if personality==soul else "性格牌｜整张地图的主语")
    draw.rounded_rectangle((465,300,935,510),radius=45,fill="#F7EBCB",outline="#D4B66C",width=3)
    label(700,405,central_role,CARDS[personality][1],SHORT[personality][0],76,"#2D2139"); heart(895,355,22)
    label(700,190,"当前年度牌｜我在哪里",CARDS[current_card][1],SHORT[current_card][0],46,"#A72E2A"); compass(830,185,24)
    if soul!=personality:
        soul_role = "性格／灵魂牌组｜共同参与" if is_three_card_group else "灵魂牌｜内在指南针"
        label(330,265,soul_role,CARDS[soul][1],SHORT[soul][0],38,"#5F4B69"); crescent(205,255,27)
    if is_three_card_group:
        label(330,430,"性格／灵魂牌组｜共同参与",CARDS[10][1],SHORT[10][0],38,"#5F4B69"); star(205,420,27)
    if profile["hidden"]:
        mentor=int(profile["hidden"][0]); label(330,430,"隐藏／导师牌｜侧翼支持",CARDS[mentor][1],SHORT[mentor][0],38,"#5F4B69"); star(205,420,27)
    sun_major=int(solar["major"]); label(1035,300,"太阳星座牌｜表达补充",CARDS[sun_major][1],SHORT[sun_major][0],38,"#79546B"); sun(1175,290,24)
    destiny=str(solar["destiny"]); label(270,565,"命运牌｜情境中的反应",destiny,MINOR_KEYWORDS[destiny[:2]][int(destiny[2:])],34,"#956C2C"); star(125,555,24)
    label(1080,575,"太阳形象牌｜我想呈现的样子",str(solar["court"]),str(solar["court_element"]),45,"#A56D1D"); sun(1260,565,22)
    number_theme=NUMBER_THEMES[soul][1].replace("；"," · ")
    label(700,685,f"生命灵数 {soul}","自律 · 选择 · 落地" if soul==8 else number_theme.split("、")[0],number_theme,30,"#5F4B69"); crescent(520,680,22)
    draw.text((72,755),"主轴不是独唱：辅助牌提供和声，年度牌告诉你此刻唱到哪一小节。",font=small_font,fill="#75627F")
    out_path=out_dir/"charts"/"personal_card_cloud.png"; out_path.parent.mkdir(parents=True,exist_ok=True); canvas.save(out_path,quality=95)
    return out_path


def card_label(number: int) -> str:
    return f"{CARDS[number][0]} {CARDS[number][1]} / {ENGLISH[number]}"


NIGHT_CARD_TRANSITIONS = {
    14: "学习在不同力量之间调和、试验与创造。",
    15: "学习辨认欲望、依附、权力与生命本能。",
    16: "学习面对结构的松动，并释放不再适用的部分。",
    17: "学习在暴露与脆弱中恢复信赖、愿景与连接。",
    18: "学习与梦境、直觉、想象和不确定性共同生活。",
}


def special_structure_data(profile: dict[str, object]) -> dict[str, object] | None:
    """Return copy and card roles only when a conditional birth structure is triggered."""
    structure = str(profile["structure"])
    personality = int(profile["personality"])
    if structure == "19-10-1":
        return {
            "kind": structure,
            "eyebrow": "RARE CONSTELLATION｜稀有牌组已开启",
            "title": "特殊牌组｜19 · 10 · 1",
            "calculation": "19 → 1 + 9 = 10 → 1 + 0 = 1",
            "cards": (19, 10, 1),
            "paragraphs": (
                "你的出生数字形成了一组较为特殊的三牌组合：XIX 太阳 → X 命运之轮 → I 魔术师。",
                "在 Mary K. Greer 的体系中，这三张牌共同参与性格与灵魂主题，而不是被简单拆分成一张性格牌和一张灵魂牌。它们指向一段富有创造力的生命旅程：太阳带来生命力、自我认同与表达愿望；命运之轮带来变化、周期与机遇；魔术师则邀请你将想法转化为语言、行动和具体创造。",
                "对这一牌组而言，重要的课题不仅是“拥有创造力”，更是学习如何辨认、组织并传达自己的创造力。自我认同、个人感受与生命目的可能紧密相连；当内在愿景和外在表达能够彼此协调时，也更容易在人际关系中清楚地呈现自己。",
                "这不是对性格的固定判断，而是一组可以在不同人生阶段持续观察的主题。",
            ),
        }
    if structure == "22-0-4":
        return {
            "kind": structure,
            "eyebrow": "RARE CONSTELLATION｜稀有牌组已开启",
            "title": "特殊牌组｜22／0 · 4",
            "calculation": "22 − 22 = 0 → 0 愚人　｜　2 + 2 = 4 → IV 皇帝",
            "cards": (22, 4),
            "paragraphs": (
                "你的出生数字落在一个特殊的临界位置：22 既可以回到 0，也可以归约为 4。",
                "在这组对应中，0 愚人作为性格牌，象征开放、自由、未知以及踏上旅程的冲劲；IV 皇帝作为灵魂牌，象征结构、秩序、责任与建立现实基础的内在需要。",
                "这两张牌之间存在一种微妙的平衡：愚人愿意走向未知，皇帝则希望建立边界与秩序；一方带来神秘、可能性和行动冲动，另一方帮助这些能量获得方向、形式与承载。",
                "我如何在保持自由与好奇的同时，为自己的选择建立稳定的结构？我又如何避免让秩序变成限制，让自由变成失去方向？这组牌不是要求你在自由与秩序之间二选一，而是邀请你学习如何让二者彼此支持。",
            ),
        }
    if structure == "night":
        return {
            "kind": structure,
            "eyebrow": "HIDDEN NIGHT CARD｜夜间牌已开启",
            "title": f"夜间牌｜{CARDS[personality][0]} {CARDS[personality][1]}",
            "calculation": f"出生数字首先归约为 {personality} → {card_label(personality)}",
            "cards": (personality,),
            "paragraphs": (
                "在这一计算结构中，不再另外推导隐藏／导师牌。",
                "从 XIV 节制到 XVIII 月亮，这五张牌被称为“夜间牌”：在节制的图像中，太阳逐渐落向地平线；经过恶魔、高塔与星星，直到月亮之后，太阳才在下一张 XIX 太阳中重新升起。",
                "“夜间”并不意味着消极、不幸或危险，而是象征一段需要与未知、矛盾和内在阴影相处的旅程。阴影不是必须被清除的缺陷，而是人格中不可分割的一部分。真正的探索，是逐渐辨认它、理解它，并学习与它建立更诚实的关系。",
                "幽暗与不确定之外，夜间牌也保存着对自然节奏的感知、对生命过程的信赖、独特的吸引力，以及在复杂经验中发现意义的能力。",
                f"这张牌特别邀请你：{NIGHT_CARD_TRANSITIONS[personality]}当答案尚未出现时，我如何保持觉察、信赖自己的感受，并继续向前？",
            ),
        }
    return None


def special_structure_markdown(profile: dict[str, object]) -> list[str]:
    data = special_structure_data(profile)
    if data is None:
        return []
    lines = ["### 🔮 隐藏彩蛋｜这组生日结构不常出现", "", f"**{data['title']}**", "", f"> `{data['calculation']}`", ""]
    for paragraph in data["paragraphs"]:
        lines.extend([str(paragraph), ""])
    return lines


def compact_card_label(number: int) -> str:
    english = ENGLISH[number].removeprefix("The ")
    return f"{CARDS[number][1]} / {english}"


def appendix_card_label(number: int) -> str:
    return APPENDIX_NAMES.get(number, f"{CARDS[number][1]} / {ENGLISH[number]}")


def major_asset(number: int) -> Path:
    return ASSET_DIR / f"major_{0 if number == 22 else number:02d}.jpg"


def copy_profile_assets(profile: dict[str, object], birth: dt.date, out_dir: Path) -> tuple[list[tuple[int, str]], list[tuple[str, str]]]:
    card_dir = out_dir / "cards"
    card_dir.mkdir(parents=True, exist_ok=True)
    personality, soul = int(profile["personality"]), int(profile["soul"])
    if profile["structure"] == "19-10-1":
        roles = [(int(number), "性格／灵魂牌组") for number in profile["core_group"]]
    else:
        roles = [(personality, "性格牌／灵魂牌")] if personality == soul else [(personality, "性格牌"), (soul, "灵魂牌")]
    roles.extend((int(value), "隐藏（导师）牌") for value in profile["hidden"])
    # Annual tables use a small image for every possible Major Arcana card.
    for number in range(1, 23):
        source = major_asset(number)
        if not source.exists():
            raise FileNotFoundError(f"缺少牌图：{source}")
        shutil.copy2(source, card_dir / source.name)
    solar = solar_symbols(birth)
    destiny_suit = str(solar["destiny"])[:2]
    destiny_rank = int(str(solar["destiny"])[2:])
    destiny_source = ASSET_DIR / f"{SUIT_CODES[destiny_suit]}_{destiny_rank:02d}.jpg"
    shutil.copy2(destiny_source, card_dir / destiny_source.name)
    minors: list[tuple[str, str]] = [(destiny_source.name, f"{solar['destiny']}｜生日区间命运牌")]
    for rank in profile["minor_ranks"]:
        for suit, suit_cn in SUITS:
            source = ASSET_DIR / f"{suit}_{int(rank):02d}.jpg"
            if not source.exists():
                raise FileNotFoundError(f"缺少牌图：{source}")
            shutil.copy2(source, card_dir / source.name)
            minors.append((source.name, f"{suit_cn}{'王牌' if int(rank) == 1 else rank}"))
    number_source = NUMBER_IMAGE_DIR / f"{int(profile['soul'])}.png"
    if not number_source.exists():
        raise FileNotFoundError(f"缺少生命灵数图：{number_source}")
    shutil.copy2(number_source, card_dir / f"number_{int(profile['soul'])}.png")
    for court_source in ASSET_DIR.glob("court_*.jpg"):
        shutil.copy2(court_source, card_dir / court_source.name)
    return roles, minors


def identity_markdown(profile: dict[str, object], args: argparse.Namespace, current: dict[str, object]) -> list[str]:
    solar = solar_symbols(args.birth_date)
    personality, soul = int(profile["personality"]), int(profile["soul"])
    structure = str(profile["structure"])
    core_group = tuple(int(v) for v in profile["core_group"])
    rows: list[tuple[str, str, str]] = []
    if structure == "19-10-1":
        rows.append(("☀️ 性格／灵魂牌组", " → ".join(card_label(n) for n in core_group), "创造力、自我认同、变化与表达共同参与"))
    else:
        rows.extend((("🦁 性格牌", card_label(personality), "较可见的人生课题"), ("💗 灵魂牌", card_label(soul), "内在目的与长期动力")))
        rows.extend(("🌑 隐藏／导师牌", card_label(int(v)), "尚待认识与整合的资源") for v in profile["hidden"])
    lines = ["## 🪞 01｜我的塔罗身份卡", "", "> [!summary] 🌙 MY TAROT PROFILE", f"> **出生日期：** {args.birth_date.strftime('%Y.%m.%d')}  ", f"> **太阳星座：** {solar['sign']}  ", f"> **核心象征：** {' × '.join(f'{CARDS[n][0]} {CARDS[n][1]}' for n in core_group)}  ", f"> **当前年度：** {card_label(int(current['card']))}", "", '<table width="100%" style="width:100%; table-layout:fixed;">', "<thead><tr><th width=\"24%\">🔮 牌位</th><th width=\"34%\">🃏 对应牌</th><th width=\"42%\">🌿 主要用途</th></tr></thead>", "<tbody>"]
    for role, label_value, purpose in rows:
        lines.append(f"<tr><td align=\"center\">{role}</td><td align=\"center\"><b>{label_value}</b></td><td>{purpose}</td></tr>")
    destiny_suit = str(solar["destiny"])[:2]
    lines.extend([f"<tr><td align=\"center\">☀️ 太阳星座牌</td><td align=\"center\"><b>{card_label(int(solar['major']))}</b></td><td>自我表达与现实中的呈现</td></tr>", f"<tr><td align=\"center\">🎯 命运牌</td><td align=\"center\"><b>{SUIT_EMOJI[destiny_suit]} {solar['destiny']}</b></td><td>具体情境中的直接反应</td></tr>", f"<tr><td align=\"center\">👑 太阳形象牌</td><td align=\"center\"><b>{solar['court']}</b></td><td>我想成为怎样的人</td></tr>", f"<tr><td align=\"center\">📍 当前年度牌</td><td align=\"center\"><b>{card_label(int(current['card']))}</b></td><td>当前阶段的练习主题</td></tr>", "</tbody></table>", ""])
    reductions, cursor = [], int(profile["total"])
    while True:
        reduced = sum(int(ch) for ch in str(cursor)); reductions.append(f"{digit_expression(cursor)} = {reduced}")
        if reduced <= 22: break
        cursor = reduced
    if structure == "19-10-1": special = "19 → 1 + 9 = 10 → 1 + 0 = 1；三张牌共同参与性格与灵魂主题。"
    elif structure == "22-0-4": special = "22 − 22 = 0 → 0 愚人；2 + 2 = 4 → IV 皇帝。自由与结构构成这组牌的核心对话。"
    elif structure == "night": special = f"{CARDS[personality][0]} {CARDS[personality][1]}属于夜间牌；阴影已包含在核心主题中，因此不另列隐藏牌。"
    elif personality == soul: special = "首个归约结果已在 1～9，因此性格牌与灵魂牌重合；同一象征分别承担外在任务与内在动力。"
    else: special = "隐藏／导师牌来自同一根数星群中未出现在归约链上的牌。"
    lines.extend(["> [!note] 🧮 完整计算链", f"> `{args.birth_date.month} + {args.birth_date.day} + {args.birth_date.year} = {profile['total']} → {' → '.join(reductions)}`  ", f"> {special}", ""])
    return lines


def profile_markdown(profile: dict[str, object], roles: list[tuple[int, str]], minors: list[tuple[str, str]], args: argparse.Namespace) -> list[str]:
    constellation, associated, principle = profile["constellation"]
    chain = " → ".join(str(value) for value in profile["chain"])
    solar = solar_symbols(args.birth_date)
    personality, soul = int(profile["personality"]), int(profile["soul"])
    hidden_labels = "、".join(card_label(int(value)) for value in profile["hidden"]) or "无额外隐藏牌"
    moon_court = COURT_CARDS.get(args.moon_sign, "资料待补充")
    rising_court = COURT_CARDS.get(args.rising_sign, "资料待补充")
    focus = "由读者在报告内自愿选择"
    response = "由读者自由书写"
    role_map: dict[int, list[str]] = defaultdict(list)
    role_map[personality].append("性格牌")
    role_map[soul].append("灵魂牌")
    for value in profile["hidden"]:
        role_map[int(value)].append("隐藏／导师牌")
    role_map[int(solar["major"])].append("太阳星座牌")
    lines = [
        "## 🔮 02｜我的个人塔罗象征语言", "",
        "<!-- 这是计算与图像底稿；交付前须按 personal-symbolic-language-writing-guide.md 完整扩写本章。 -->", "",
        "> 以下依照用户提供的 Mary K. Greer《Tarot for Your Self》“个人塔罗象征的指引和启发”工作页逐步展开。它用于建立个人象征语言，不是固定人格诊断。", "",
        "### 🧮 牌位与计算", "",
        f"- 出生加总：`出生月 + 出生日 + 出生年 = {profile['total']} → {chain}`",
        f"- 性格牌：**{card_label(personality)}**——你在外部世界较可见的学习方式、人生方向与行动策略。",
        f"- 灵魂牌：**{card_label(soul)}**——你的内在目的、本质与长期动力。",
        f"- 隐藏／导师牌：**{hidden_labels}**——可能以恐惧、抗拒、投射或未被看见的能力出现；被认识后也可能成为重要资源。",
        f"- 星群：**{constellation}**",
        f"- 关联对应：**{'、'.join(card_label(int(value)) for value in associated)}**",
        f"- 核心特质：**{principle}**", "",
    ]
    for number, card_roles in role_map.items():
        image_number = 0 if number == 22 else number
        emojis = "".join(ROLE_EMOJI[role] for role in card_roles)
        joined_roles = " × ".join(card_roles)
        role_definition = "；".join({
            "性格牌": "较可见的人生课题与学习方式",
            "灵魂牌": "内在目的与长期动力",
            "隐藏／导师牌": "可能从抗拒走向整合的资源",
            "太阳星座牌": "自我表达与向外呈现",
        }[role] for role in card_roles)
        lines.extend([
            f"### {emojis} {card_label(number)}｜{joined_roles}", "",
            '<table width="100%" style="width:100%; table-layout:fixed;"><tr>',
            f'<td width="160" align="center"><img src="cards/major_{image_number:02d}.jpg" width="135"><br><b>{CARDS[number][0]} {CARDS[number][1]}</b></td>',
            f'<td><b>🔮 身份：</b>{joined_roles}<br><b>✨ 建设方向：</b>{CARDS[number][2]}<br><b>🌑 观察方向：</b>{CARDS[number][3]}<br><b>💭 核心问题：</b>这张牌在不同牌位中，分别邀请我练习什么？</td>',
            "</tr></table>", "",
            "> [!abstract] 📖 Mary 怎么说", f"> 在这份图谱中，这张牌承担“{joined_roles}”的牌位功能：{role_definition}。原书相关年度课题全文见第 08 章。", "",
            "> [!interpretation] 🌿 放进你的图谱里", f"> 你可以观察：{CARDS[number][2]}。这是可反复检验的象征线索，不是固定人格判断。", "",
            "> [!warning] 🌑 可以留意", f"> {CARDS[number][3]}。", "",
            "> [!question] 💭 可以问自己", "> - 最近哪件具体事情最需要我练习这张牌的建设性方向？", "> - 我是在使用它，还是在过度使用／回避它？", "",
        ])
        if "性格牌" in card_roles and "灵魂牌" in card_roles:
            lines.extend([
                "> [!insight] ✨ 当性格牌与灵魂牌重合",
                "> 同一象征同时承担外在学习任务与内在长期动力，可能带来集中与清晰，也值得留意是否把自我认同收得过紧。基础牌义只呈现一次，两个牌位的功能分别观察。", "",
            ])
    lines.extend(["### 🔢 生命灵数与机会牌", "", f"生命灵数 **{soul}** 把同一数字主题带入四个经验领域；根数 1 时同时保留四张王牌与四张 10。", "", "<table width=\"100%\" style=\"width:100%; table-layout:fixed;\">"])
    for offset in range(0, len(minors), 4):
        lines.append("<tr>")
        for filename, label in minors[offset:offset + 4]:
            lines.append(f'<td align="center"><img src="cards/{filename}" width="115"><br>{label}</td>')
        lines.append("</tr>")
    lines.extend([
        "</table>", "", f"### 🎯 {SUIT_EMOJI[str(solar['destiny'])[:2]]} {solar['destiny']}｜命运牌", "",
        f"> [!abstract] 📖 Mary 怎么说\n> 命运牌用于观察具体情境中较本能、直接的冲动、欲望与反应；它不同于性格牌的人生课题与灵魂牌的长期动力。", "",
        f"> [!interpretation] 🌿 放进你的图谱里\n> 生日位于 {solar['sign']} 的对应区间，命运牌为 **{solar['destiny']}**。可以把它当作反应倾向的观察镜面，而不是宿命标签。", "",
        "### 👑 形象／潜力牌", "",
        f"- ☀️ 个人潜力牌（太阳）：**{solar['sign']} → {solar['court']}**",
        f"- 🌙 内在导师牌（月亮）：**{moon_court}**",
        f"- 🌅 个人表达模式牌（上升）：**{rising_court}**", "",
        "> 月亮或上升未知时保持“待补充”，不得根据性格猜测。", "",
        "### 💬 与焦点牌对话", "",
        f"- 已选焦点牌：**{focus}**",
        "- Greer 式提问：**在此生我需要学习的事物中，你能教导我什么？**",
        f"- 读者回答：{response}", "",
    ])
    return lines


def synthesis_markdown(profile: dict[str, object], args: argparse.Namespace, current_card: int) -> list[str]:
    soul = int(profile["soul"])
    hidden = "、".join(CARDS[int(v)][1] for v in profile["hidden"]) or "核心牌自身包含的阴影面"
    return [
        "## 🧩 03｜把这些牌放在一起", "",
        "### ✨ 核心主题", "",
        COMBINATION_ANALYSES[soul], "",
        f"- **主题一｜外在课题与内在动力**：比较 {CARDS[int(profile['personality'])][1]} 与 {CARDS[soul][1]} 分别如何出现在行动和满足感中。",
        f"- **主题二｜尚待整合的资源**：把 {hidden} 放回整组牌中，观察它何时像阻力、何时能成为支持。",
        f"- **主题三｜表达与现实反应**：比较太阳星座牌、命运牌与核心牌在同一事件中承担的不同功能。", "",
        "### 🌑 可能的张力", "",
        "> [!warning] 🌑 观察，而非定论",
        "> 同一象征可能在不同情境中表现为资源、过度使用或回避。请结合真实事实、身体感受和关系反馈来验证，不要用牌替代判断。", "",
        "### 💭 给我的问题", "",
        "> [!question] 💭 塔罗日记",
        "> - 最近一次重要选择里，我最先使用的是哪张牌的策略？",
        "> - 哪种身体感受会提醒我正在逞强、拖延或失去边界？",
        "> - 我在哪段关系中最容易把自己的选择权交出去？",
        "> - 哪项资源已经存在，却仍被我当成风险或缺点？",
        "> - 如果把当前年度牌当作练习，我本周能验证哪一个小行动？",
        "> - 三个月后回看，我希望留下什么可核对的记录？", "",
    ]


def year_card(birth: dt.date, target_year: int) -> tuple[int, int]:
    total = birth.month + birth.day + target_year
    return total, reduce_card(total)


def anniversary(year: int, birth: dt.date) -> dt.date:
    try:
        return dt.date(year, birth.month, birth.day)
    except ValueError:
        if birth.month == 2 and birth.day == 29:
            return dt.date(year, 2, 28)
        raise


def age_on(date_value: dt.date, birth: dt.date) -> int:
    before_anniversary = date_value < anniversary(date_value.year, birth)
    return date_value.year - birth.year - int(before_anniversary)


def phase_for(age: int) -> str:
    for low, high, text in PHASES:
        if low <= age <= high:
            return text
    return "当前阶段：结合真实身体、关系、责任与支持条件理解牌义"


def parse_nodes(values: list[str], birth: dt.date) -> dict[int, list[str]]:
    result: dict[int, list[str]] = {}
    for raw in values:
        match = NODE_RE.match(raw.strip())
        if not match:
            raise ValueError(f"人生节点格式错误：{raw!r}；应为 YYYY=事件 或 YYYY-MM-DD=事件")
        when, label = match.groups()
        label = label.strip()
        if not label:
            raise ValueError(f"人生节点缺少事件名称：{raw!r}")
        if len(when) == 4:
            start_year = int(when)
            display = f"{when}：{label}"
        else:
            event_date = parse_date(when)
            if event_date < birth:
                raise ValueError(f"人生节点早于出生日期：{raw!r}")
            event_age = age_on(event_date, birth)
            start_year = birth.year + event_age
            display = f"{when}：{label}"
        result.setdefault(start_year, []).append(display)
    return result


def _period_text(rows: list[dict[str, object]], start: int, length: int) -> str:
    first, last = rows[start], rows[start + length - 1]
    return f"{first['age']}～{last['age']} 岁（{first['year']}～{last['year']}）"


def analyze_loops(rows: list[dict[str, object]]) -> dict[str, object]:
    """Extract up to three distinct dominant repeats and every high-to-low reset."""
    cards = [int(row["card"]) for row in rows]
    candidates: list[dict[str, object]] = []
    for length in range(4, 9):
        windows: dict[tuple[int, ...], list[int]] = defaultdict(list)
        for start in range(0, len(cards) - length + 1):
            windows[tuple(cards[start:start + length])].append(start)
        for sequence, starts in windows.items():
            if len(starts) >= 2:
                node_hits = sum(bool(rows[i]["nodes"]) for start in starts for i in range(start, start + length))
                candidates.append({"sequence": sequence, "starts": starts, "length": length, "node_hits": node_hits})
    candidates.sort(key=lambda item: (-len(item["starts"]), -int(item["length"]), -int(item["node_hits"]), item["starts"][0]))

    def too_similar(left: tuple[int, ...], right: tuple[int, ...]) -> bool:
        if len(left) <= len(right) and any(tuple(right[i:i + len(left)]) == left for i in range(len(right) - len(left) + 1)):
            return True
        if len(right) <= len(left) and any(tuple(left[i:i + len(right)]) == right for i in range(len(left) - len(right) + 1)):
            return True
        a = set(zip(left, left[1:])); b = set(zip(right, right[1:]))
        return bool(a and b) and len(a & b) / min(len(a), len(b)) >= 0.50

    exact: list[dict[str, object]] = []
    for candidate in candidates:
        sequence = tuple(candidate["sequence"])
        if not any(too_similar(sequence, tuple(kept["sequence"])) for kept in exact):
            exact.append(candidate)
        if len(exact) >= 3:
            break

    drop_indices = [index for index in range(len(cards) - 1) if cards[index + 1] < cards[index]]
    declines: list[dict[str, object]] = []
    for pos, drop in enumerate(drop_indices):
        segment_start = drop + 1
        segment_end = drop_indices[pos + 1] if pos + 1 < len(drop_indices) else len(cards) - 1
        declines.append({
            "from": cards[drop], "to": cards[segment_start], "drop": drop,
            "segment_start": segment_start, "segment_end": segment_end,
            "duration": segment_end - segment_start + 1,
        })
    return {"exact": exact, "declines": declines}


def _node_context(rows: list[dict[str, object]], starts: list[int], length: int) -> tuple[str, str]:
    facts: list[str] = []
    for start in starts:
        for row in rows[start:start + length]:
            facts.extend(str(node) for node in row["nodes"])
    if facts:
        unique = list(dict.fromkeys(facts))
        shown = unique[:2]
        suffix = f"；另有 {len(unique)-2} 个重合节点" if len(unique) > 2 else ""
        return "已知节点：" + "；".join(shown) + suffix, "可比较这些节点前后，你采用的策略、获得的支持与承受的压力有何异同。"
    return "暂无已知节点可供个案化解释。", "可回想这些阶段是否出现过相似问题；若没有，也不必强行对应。"


def loop_markdown(rows: list[dict[str, object]], analysis: dict[str, object]) -> list[str]:
    lines = [
        "### 🔁 Lifetime Loops｜重复周期", "",
        "> 这里只保留出现次数最多且彼此不冗余的三条主循环。循环是可比较的象征节奏，不表示具体事件必然重演。", "",
    ]
    exact = analysis["exact"]
    if not exact:
        lines.extend(["在当前年龄范围内，没有长度至少为 4 的完整重复连续序列。", ""])
    for index, item in enumerate(exact, 1):
        seq = " → ".join(compact_card_label(card) for card in item["sequence"])
        readable = " → ".join(SHORT[int(card)][0].split("，")[0] for card in item["sequence"])
        periods = "；".join(_period_text(rows, start, int(item["length"])) for start in item["starts"])
        first, last = int(item["sequence"][0]), int(item["sequence"][-1])
        middle = "、".join(CARDS[int(card)][1] for card in item["sequence"][1:-1])
        node_fact, _ = _node_context(rows, list(item["starts"]), int(item["length"]))
        node_line = "" if node_fact.startswith("暂无") else f"- **节点提示**：{node_fact.removeprefix('已知节点：')}"
        lines.extend([
            f"### 🌀 Loop {index:02d}｜{readable}", "",
            f"**{seq}**", "",
            f"🔁 **重复出现：** {len(item['starts'])} 次", "",
            f"📅 **出现阶段：** {periods}", "",
            f"🌿 **可以怎样理解：** 从 {CARDS[first][1]} 的“{SHORT[first][0]}”起步，经由 {middle} 的连续转换，最终落在 {CARDS[last][1]} 的“{SHORT[last][0]}”。这像一条从启动方式逐步走向收束课题的生命节奏；每次重现时，可以比较自己是否用了不同资源与边界。",
        ])
        if node_line:
            lines.append(node_line)
        lines.append("")
    lines.extend([
        "### ↘️ Reset｜下降段与起点转换", "",
        "> [!info] ↘️ 什么是 Reset？", "> 年度牌并不是简单从 1 一直走到 22。在数字归约过程中，会周期性出现下降和新的起点。", ">", "> 这些节点适合用来观察：**一个长期阶段如何结束，下一段生命节奏又从哪里重新开始。**它们不是外部命运事件。", "",
        "| 发生年龄／年份 | 起点转换 | 下一段持续 | 下一段终点 |", "|---|---|---:|---|",
    ])
    for item in analysis["declines"]:
        drop = int(item["drop"]); end = int(item["segment_end"])
        lines.append(
            f"| {rows[drop]['age']}→{rows[drop+1]['age']} 岁（{rows[drop]['year']}→{rows[drop+1]['year']}） | "
            f"{card_label(int(item['from']))} → {card_label(int(item['to']))} | {item['duration']} 年 | "
            f"{rows[end]['age']} 岁（{rows[end]['year']}）·{card_label(int(rows[end]['card']))} |"
        )
    lines.append("")
    return lines


def annual_appendix_markdown() -> list[str]:
    lines = ["## 📜 08｜Mary K. Greer 原书依据", "", "> [!abstract] 📖 年度牌课题完整转写", "> 以下据用户提供的 Mary K. Greer《Tarot for Your Self》中文书页逐条转写；繁体字统一为简体，内容范围与顺序完整保留。它们是探索主题，不是事件预言。", "", "| 号 | 牌名 | 原书页所列年度课题 |", "|---:|---|---|"]
    for number in range(1, 23):
        label_no = "22／0" if number == 22 else str(number)
        lines.append(f"| {label_no} | {appendix_card_label(number)} | {ANNUAL_THEMES[number]} |")
    lines.append("")
    return lines


def svg_text(x: float, y: float, text_value: str, **attrs: object) -> str:
    pairs = [f'{key.replace("_", "-")}="{html.escape(str(value))}"' for key, value in attrs.items()]
    return f'<text x="{x:.1f}" y="{y:.1f}" {" ".join(pairs)}>{html.escape(text_value)}</text>'


def make_chart(
    rows: list[dict[str, object]],
    path: Path,
    current_age: int | None,
) -> None:
    left, right, top, bottom = 230, 45, 95, 155
    width = max(1180, left + right + max(1, len(rows) - 1) * 54)
    height = 760
    plot_w, plot_h = width - left - right, height - top - bottom

    def x_for(index: int) -> float:
        return left + (plot_w / max(1, len(rows) - 1)) * index

    def y_for(card: int) -> float:
        return top + (22 - card) / 21 * plot_h

    title = f"{rows[0]['age']}～{rows[-1]['age']} 岁年度牌走势（{rows[0]['year']}～{rows[-1]['year']}）"
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
        f"<title>{html.escape(title)}</title>",
        "<desc>横轴为周岁，纵轴为大阿尔卡那牌号；愚人按22绘制。</desc>",
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<g font-family="Microsoft YaHei, PingFang SC, Noto Sans CJK SC, sans-serif" fill="#000000">',
        svg_text(width / 2, 34, title, text_anchor="middle", font_size="20", font_weight="700"),
        svg_text(width / 2, 58, "Mary K. Greer 年度牌｜RWS：VIII 力量、XI 正义", text_anchor="middle", font_size="12", fill="#6b7280"),
    ]

    for card in range(1, 23):
        y = y_for(card)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" stroke="#000000" stroke-opacity="0.30" stroke-width="1"/>')
        label = ("22/0 " if card == 22 else f"{card} ") + compact_card_label(card)
        parts.append(svg_text(left - 12, y + 4, label, text_anchor="end", font_size="10", fill="#000000"))

    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#000000" stroke-width="1.5"/>')
    parts.append(f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#000000" stroke-width="1.5"/>')

    points = []
    for index, row in enumerate(rows):
        x, y = x_for(index), y_for(int(row["card"]))
        points.append(f"{x:.1f},{y:.1f}")
        parts.append(f'<line x1="{x:.1f}" y1="{height-bottom}" x2="{x:.1f}" y2="{height-bottom+5}" stroke="#000000"/>')
        parts.append(svg_text(x + 3, height - bottom + 20, str(row["age"]), transform=f"rotate(45 {x+3:.1f} {height-bottom+20:.1f})", font_size="10", fill="#000000"))

    parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="#000000" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>')

    for index, row in enumerate(rows):
        x, y = x_for(index), y_for(int(row["card"]))
        has_node = bool(row["nodes"])
        is_current = current_age is not None and int(row["age"]) == current_age
        radius = 7 if (has_node or is_current) else 4
        fill = "#ffffff" if has_node else "#000000"
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="{fill}" stroke="#000000" stroke-width="{3 if is_current else 2}"/>')
        level = index % 3
        label_y = y - (16 + level * 12) if index % 2 == 0 else y + (24 + level * 12)
        label_y = max(82, min(height - bottom - 8, label_y))
        label = compact_card_label(int(row["card"]))
        parts.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{label_y + (-4 if label_y < y else 4):.1f}" stroke="#000000" stroke-width="0.7"/>')
        parts.append(svg_text(x, label_y, label, text_anchor="middle", font_size="8", font_weight="700", fill="#000000"))
        if has_node:
            node_label = "；".join(str(value).split("：", 1)[-1] for value in row["nodes"])
            node_label = node_label if len(node_label) <= 14 else node_label[:13] + "…"
            parts.append(svg_text(x, max(74, y - 42), node_label, text_anchor="middle", font_size="9", font_weight="700", fill="#6b4e16"))
        elif is_current:
            parts.append(svg_text(x, max(74, y - 42), "当前", text_anchor="middle", font_size="9", font_weight="700", fill="#000000"))

    parts.extend([
        svg_text(width / 2, height - 20, "周岁", text_anchor="middle", font_size="13", font_weight="700"),
        svg_text(22, height / 2, "大阿尔卡纳", transform=f"rotate(-90 22 {height/2:.1f})", text_anchor="middle", font_size="13", font_weight="700"),
        svg_text(left, height - 4, "空心圆＝人生节点　粗边圆＝当前年龄　实心圆＝普通年度", font_size="11", fill="#000000"),
        "</g>",
        "</svg>",
    ])
    path.write_text("\n".join(parts), encoding="utf-8")


def safe_period(start_year: int, birth: dt.date) -> tuple[dt.date, dt.date]:
    start = anniversary(start_year, birth)
    next_start = anniversary(start_year + 1, birth)
    return start, next_start - dt.timedelta(days=1)


def current_location_markdown(args: argparse.Namespace, current_age: int, current: dict[str, object]) -> list[str]:
    birth = args.birth_date
    start, end = safe_period(int(current["year"]), birth)
    if args.year_boundary == "calendar":
        period_text = f"{current['year']}-01-01 → {current['year']}-12-31（自然年）"
    elif args.year_boundary == "both":
        period_text = f"自然年 {current['year']}-01-01 → {current['year']}-12-31；生日周期 {start.isoformat()} → {end.isoformat()}"
    else:
        period_text = f"{start.isoformat()} → {end.isoformat()}（生日周期）"
    nearby = []
    for offset, marker in ((-1, "⏪"), (0, "📍"), (1, "⏩")):
        year = int(current["year"]) + offset
        _, number = year_card(birth, year)
        label = f"{CARDS[number][0]} {CARDS[number][1]}"
        nearby.append(f"{marker} {year} · {label}" if offset else f"{marker} 【{year} · {label}】")
    number = int(current["card"])
    return [
        "## 📍 04｜我现在在哪里？", "",
        "> [!important] 📍 YOU ARE HERE",
        f"> **{current_age} 岁 · {current['year']}**  ",
        f"> **{CARDS[number][0]} · {CARDS[number][1]}**  ",
        f"> 🌿 **这一阶段的核心动作：{SHORT[number][0]}**  ",
        f"> `{period_text}`", "",
        "### ⏪ 上一年度 · 📍 当前年度 · ⏩ 下一年度", "",
        f"**{'　→　'.join(nearby)}**", "",
        f"> [!warning] ⚠️ 可以留意\n> {SHORT[number][1]}。这是一项观察提示，不是对事件的预测。", "",
    ]


def annual_lookup_markdown(rows: list[dict[str, object]], current_age: int, birth: dt.date) -> list[str]:
    full_life = int(rows[0]["age"]) == 0 and int(rows[-1]["age"]) == 100 and len(rows) == 101
    title = "## 📚 06｜0～100 岁年度牌查询表" if full_life else f"## 📚 06｜{rows[0]['age']}～{rows[-1]['age']} 岁年度牌查询表"
    lines = [
        title, "",
        "> [!tip] 🔎 怎么查？", "> 想查某个年龄，看「🎂 年龄」列；想查某一年，看「📆 年份」列。", "> ⭐ 表示你提供的重要人生节点，📍 表示当前所在年份。两者同时发生时显示 ⭐📍。", "",
    ]
    for band_start, band_end, emoji in AGE_BANDS:
        selected = [row for row in rows if band_start <= int(row["age"]) <= band_end]
        if not selected:
            continue
        start_age, end_age = int(selected[0]["age"]), int(selected[-1]["age"])
        lines.extend([
            f"### {emoji} {start_age}～{end_age} 岁｜{birth.year + start_age}～{birth.year + end_age}", "",
            '<table width="100%" style="width:100%; table-layout:fixed;">',
            "<thead><tr>",
            '<th width="12%" align="center">🎂 年龄</th>',
            '<th width="18%" align="center">📆 年份</th>',
            '<th width="25%" align="center">🧮 核算</th>',
            '<th width="45%" align="center">🔮 年度牌</th>',
            "</tr></thead>", "<tbody>",
        ])
        for row in selected:
            age, year, number = int(row["age"]), int(row["year"]), int(row["card"])
            marker_text = ("⭐" if row["nodes"] else "") + ("📍" if age == current_age else "")
            markers = f" {marker_text}" if marker_text else ""
            image_number = 0 if number == 22 else number
            values = (
                str(age), f"{year}{markers}", f"{row['total']} → {number}",
                f'<img src="cards/major_{image_number:02d}.jpg" width="42"><br><b>{CARDS[number][0]}. {CARDS[number][1]}</b>',
            )
            is_current = age == current_age
            if is_current:
                values = (f"<b>{values[0]}</b>", f"<b>{values[1]}</b>", f"<b>{values[2]}</b>", values[3])
            lines.extend([
                '<tr style="background:#f6f0ff;">' if is_current else "<tr>",
                f'<td align="center">{values[0]}</td>', f'<td align="center">{values[1]}</td>',
                f'<td align="center">{values[2]}</td>', f'<td align="center">{values[3]}</td>',
                "</tr>",
            ])
        lines.extend(["</tbody></table>", ""])
    return lines


def profile_markdown(profile: dict[str, object], roles: list[tuple[int, str]], minors: list[tuple[str, str]], args: argparse.Namespace) -> list[str]:
    """Render the final three-module symbolic-language chapter for Markdown."""
    constellation, associated, principle = profile["constellation"]
    solar = solar_symbols(args.birth_date)
    soul = int(profile["soul"])
    role_map: dict[int, list[str]] = defaultdict(list)
    if profile["structure"] == "19-10-1":
        for number in profile["core_group"]: role_map[int(number)].append("性格／灵魂牌组")
    else:
        role_map[int(profile["personality"])].append("性格牌")
        role_map[soul].append("灵魂牌")
        for number in profile["hidden"]: role_map[int(number)].append("隐藏／导师牌")
    role_map[int(solar["major"])].append("太阳星座牌")
    if profile["structure"] == "19-10-1":
        opening = "这组三张特殊出生牌共同承担性格与灵魂主题；太阳、命运之轮与魔术师是一条连续的创造与表达线，不拆成普通的性格牌、灵魂牌或导师牌。"
    elif profile["structure"] == "night":
        opening = "性格牌与灵魂牌共同构成主轴；夜间牌已经把阴影经验包含在核心结构中，因此本章不另设隐藏／导师牌。"
    elif profile["structure"] == "22-0-4":
        opening = "愚人与皇帝分别承担性格牌与灵魂牌：自由与结构需要彼此支持，本章不增设没有计算依据的导师牌。"
    else:
        opening = "这些牌不是一份静止的人格清单。性格牌是主轴，灵魂牌与导师牌从内侧协助，太阳星座牌补充你怎样表达自己。"
    lines = ["## 🔮 02｜我的个人塔罗象征语言", "", opening, "", f"> [!abstract] 📖 星群主题\n> **{constellation}｜{principle}**。关联牌为 {'、'.join(card_label(int(v)) for v in associated)}。", ""]
    for number, card_roles in role_map.items():
        joined = " × ".join(card_roles); image_number = 0 if number == 22 else number
        lines.extend([f"### {card_label(number)}｜{joined}", "", '<table width="100%" style="width:100%; table-layout:fixed;"><tr>', f'<td width="160" align="center"><img src="cards/major_{image_number:02d}.jpg" width="135"><br><b>{CARDS[number][0]} {CARDS[number][1]}</b></td>', f'<td><b>{joined}是什么意思？</b><br>{"<br>".join(ROLE_DEFINITIONS[r] for r in card_roles)}<br><br><b>🌿 星群主题：</b>{constellation}</td>', "</tr></table>", "", "**牌面中的象征**", ""])
        for name, meaning in CARD_SYMBOLS[number]:
            lines.append(f"- {symbol_emoji(name)} **{name}**：{meaning}")
        lines.extend(["", "**牌意解读**", ""])
        for icon, heading, text_value in interpretation_points(number, card_roles):
            lines.append(f"- {icon} **{heading}：** {text_value}")
        lines.append("")
    geometry, number_theme = NUMBER_THEMES[soul]
    opportunity_cards = [item for item in minors if "命运牌" not in item[1]]
    full_number = "；".join(f"**{heading}：**{meaning}" for heading, meaning in NUMBER_FULL[soul])
    lines.extend(["### 🔢 生命灵数与机会牌｜数字如何进入四种元素", "", '<table width="100%" style="width:100%; table-layout:fixed;"><tr>', f'<td width="180" align="center"><img src="cards/number_{soul}.png" width="150"><br><b>生命灵数 {soul}</b></td>', f'<td><b>数字图形：</b>{geometry}<br><br>{full_number}</td>', "</tr></table>", "", f"数字 **{soul}** 把“{number_theme}”带进行动、情感、思考与现实四个领域。", "", '<table width="100%" style="width:100%; table-layout:fixed;">'])
    for offset in range(0, len(opportunity_cards), 4):
        lines.append("<tr>")
        for filename, label in opportunity_cards[offset:offset + 4]:
            suit, rank, title, keywords = opportunity_meta(label)
            domain = {"权杖":"火／行动与意志", "圣杯":"水／情感与关系", "宝剑":"风／思考与判断", "星币":"土／现实、身体与实践"}[suit]
            meaning = OPPORTUNITY_MEANINGS[rank][suit]
            lines.append(f'<td align="center" valign="top"><img src="cards/{filename}" width="115"><br><b>{SUIT_EMOJI[suit]} {label}｜{title}</b><br><b>关键词：{keywords}</b><br>{domain}<br>{meaning}</td>')
        lines.append("</tr>")
    destiny_file = next(name for name, label in minors if "命运牌" in label)
    lines.extend(["</table>", "", "**四牌合看：** 权杖问“我要怎样行动”，圣杯问“我如何感受与连接”，宝剑问“我怎样理解和决定”，星币问“我如何落实并照顾现实”。四张牌共同显示同一生命灵数在四个生活领域里的不同练习。", "", f"### 🎯 命运牌｜生日落入的 {solar['destiny']}", "", '<table width="100%" style="width:100%; table-layout:fixed;"><tr>', f'<td width="170" align="center"><img src="cards/{destiny_file}" width="135"><br><b>{solar["destiny"]}</b></td>', f'<td><b>出生旬区：</b>{solar["sign"]}第 {solar["decan"]} 旬，约 {solar["degree_interval"]}<br><br><b>占星组合：</b>{PLANET_SYMBOL[str(solar["ruler"])]} {solar["ruler"]} × {SIGN_SYMBOL[str(solar["sign"])]} {solar["sign"]}<br><br><b>传统牌名：</b>{MINOR_TITLES[int(str(solar["destiny"])[2:])][str(solar["destiny"])[:2]]}</td>', "</tr></table>", "", "![塔罗占星图：金色区域为出生旬区，红点为生日近似位置](charts/astrology_decan.png)", "", f"**牌面中的象征：** {destiny_symbol_text(str(solar['destiny']))}", "", f"**命运牌大意：** {OPPORTUNITY_MEANINGS[int(str(solar['destiny'])[2:])][str(solar['destiny'])[:2]]}", ""])
    if solar["sabian"]:
        lines.extend([f"**生日对应的撒比恩象征：** {solar['sign']} {solar['degree_interval']}：{solar['sabian']}", "", f"这个场景邀请人把抽象知识带回可观看、可讨论的现实。它与 {solar['destiny']} 的呼应在于：理解不是独自占有答案，而是让观察、协作与建造彼此校正。", ""])
    lines.extend(["### 👑 形象牌｜太阳、月亮与上升的宫廷人物", "", "数字牌更像情境，宫廷牌则像活生生的人物：有气质、习惯、动作和表达方式，仿佛身体里住着几位会在不同场合接手方向盘的人。", ""])
    positions = image_positions(args, solar)
    for position in positions:
        sign_name = position["sign"]
        portrait_text = bold_selected_cards(court_portrait(position), [position["card"]])
        lines.extend([f"**{position['role']}**", "", '<table width="100%" style="width:100%; table-layout:fixed;"><tr>', f'<td width="150" align="center"><img src="cards/{court_asset_name(position["card"])}" width="120"><br><b>{position["card"]}</b></td>', f'<td>{SIGN_SYMBOL[sign_name]} <b>{position_label(position)}</b><br><br>✨ <b>元素配方：</b>{position["element"]}<br><br>🎭 {portrait_text}</td>', "</tr></table>", ""])
    if len(positions) < 3:
        lines.extend(["如果以后补充月亮或上升星座，或已经计算好的月亮／上升黄经，还可以让另外两位宫廷人物进入这张地图。", ""])
    lines.extend(["### 💬 焦点牌图像对话", "", "从报告里任意选择一张此刻最吸引你的牌，给自己七分钟，沿着下面的问题自由书写：", "", "1. 我选择了哪张牌？为什么此刻选择它？", "2. 我最先看见了哪个人物、颜色、动作或物件？", "3. 如果这张牌能够说话，我想问它什么？它可能怎样回答？", "4. 它让我想起了什么经历、关系、感受或行为模式？", "5. 我想把哪一项观察带回现实生活？", ""])
    return lines


def synthesis_markdown(profile: dict[str, object], args: argparse.Namespace, current_card: int) -> list[str]:
    solar = solar_symbols(args.birth_date); soul = int(profile["soul"])
    core_names = [CARDS[int(v)][1] for v in profile["core_group"]]
    hidden_names = [CARDS[int(v)][1] for v in profile["hidden"]]
    support = f"**{CARDS[soul][1]}**与**{CARDS[int(solar['major'])][1]}**共同把“{SHORT[soul][0]}”带向可见的表达。"
    tension = f"**{core_names[0]}**强调{SHORT[int(profile['personality'])][0]}，而**{solar['destiny']}**把注意力拉回具体情境；两者的拉扯在于理想方向与眼前回应如何互相校正。"
    if hidden_names: tension += f" **{hidden_names[0]}**加入后，原本被回避的部分也可能成为推进关系或行动的资源。"
    conclusion = formatted_combination(soul)
    if profile["structure"] == "19-10-1":
        identity_line = "- **我是谁：** **太阳 × 命运之轮 × 魔术师**共同构成性格／灵魂牌组；生命力、周期变化与有意识的创造彼此牵动。"
    elif profile["structure"] == "night":
        identity_line = f"- **我是谁：** 夜间牌 **{CARDS[int(profile['personality'])][1]}**与灵魂牌 **{CARDS[soul][1]}**共同构成主轴；阴影属于核心经验，不另设导师牌。"
    else:
        identity_line = "- **我是谁：** 性格牌 **"+CARDS[int(profile['personality'])][1]+"** 位于中央，是最常使用、也最需要持续精炼的生命语言。"
    return ["## 🧩 03｜把这些牌放在一起", "", "![塔罗关系词云：核心牌、当前年度与形象牌彼此回应](charts/personal_card_cloud.png)", "", identity_line, f"- **内在协助：** {support}", f"- **现实互动：** {tension}", f"- **我在哪里：** 当前年度牌 **{CARDS[current_card][1]}** 把整组牌带到“{SHORT[current_card][0]}”的现场。", f"- **我想怎样被看见：** **{solar['court']}** 与 **{CARDS[int(solar['major'])][1]}**共同补充外在表达。", "", f"> **综合结论：** {conclusion} 这张地图的重点不是选出一张“最好的牌”，而是让主轴、辅助与当下课题在同一张桌上说话。", ""]


def analyze_loops(rows: list[dict[str, object]], profile: dict[str, object] | None = None, current_age: int | None = None) -> dict[str, object]:
    cards = [int(row["card"]) for row in rows]
    drops = [i for i in range(len(cards)-1) if cards[i+1] < cards[i]]
    bounds = [0] + [i+1 for i in drops] + [len(rows)]
    stages = [{"start": bounds[i], "end": bounds[i+1]-1} for i in range(len(bounds)-1)]
    active = next((i for i,s in enumerate(stages) if current_age is not None and int(rows[s["start"]]["age"]) <= current_age <= int(rows[s["end"]]["age"])), 0)
    core_returns = []
    if profile:
        seen = set()
        for number in profile["core_group"]:
            number = int(number)
            if number in seen: continue
            seen.add(number)
            core_returns.append({"card": number, "ages": [int(r["age"]) for r in rows if int(r["card"]) == number]})
    declines = []
    for pos, drop in enumerate(drops):
        segment_start = drop + 1
        segment_end = drops[pos + 1] if pos + 1 < len(drops) else len(cards) - 1
        declines.append({"from": cards[drop], "to": cards[segment_start], "drop": drop, "segment_start": segment_start, "segment_end": segment_end, "duration": segment_end-segment_start+1})
    return {"exact": [], "declines": declines, "stages": stages, "active_stage": active, "core_returns": core_returns}


def loop_markdown(rows: list[dict[str, object]], analysis: dict[str, object], current_age: int | None = None) -> list[str]:
    lines = ["### 🔁 生命牌序中的回声", "", "**CORE CARD RETURNS｜核心牌回归**", ""]
    for item in analysis["core_returns"]:
        number = int(item["card"]); ages = " · ".join(f"{age} 岁" for age in item["ages"])
        lines.extend([f"- **{card_label(number)}**｜{ages}", f"  同一主题会在不同年龄以不同成熟度回来；这里记录的是牌序回归，不预设事件重复。"])
    active = int(analysis["active_stage"]); stage = analysis["stages"][active]
    arc_rows = rows[int(stage["start"]):int(stage["end"])+1]
    lines.extend(["", "**CURRENT ARC｜当前十年牌序**", "", " | ".join(f"{r['age']}岁 · {CARDS[int(r['card'])][1]} · {SHORT[int(r['card'])][0].split('，')[0]}" for r in arc_rows), "", f"当前年度位于这段牌序的{'开端' if current_age == int(arc_rows[0]['age']) else '收束' if current_age == int(arc_rows[-1]['age']) else '推进阶段'}。前牌留下的动作会进入当前牌，下一张牌则提示这段过程将从哪里继续。", "", "**RESET｜阶段总览与下一次起点转换**", "", "| 阶段 | 年龄区间 | 起点牌 | 终点牌 |", "|---:|---|---|---|"])
    for index, item in enumerate(analysis["stages"], 1):
        first, last = rows[int(item["start"])], rows[int(item["end"])]
        marker = "📍 " if index-1 == active else ""
        lines.append(f"| {marker}{index} | {first['age']}～{last['age']} 岁 | {card_label(int(first['card']))} | {card_label(int(last['card']))} |")
    lines.append("")
    return lines


def current_location_markdown(args: argparse.Namespace, current_age: int, current: dict[str, object], loop_analysis: dict[str, object]) -> list[str]:
    birth = args.birth_date; number = int(current["card"]); start, end = safe_period(int(current["year"]), birth)
    nearby=[]
    for offset, marker in ((-1,"⏪ 上一年度"),(0,"📍 当前年度"),(1,"⏩ 下一年度")):
        year=int(current["year"])+offset; _,card=year_card(birth,year); nearby.append((marker,year,card))
    active=int(loop_analysis["active_stage"]); stage=loop_analysis["stages"][active]
    stage_start=int(stage["start"])+args.age_start; stage_end=int(stage["end"])+args.age_start
    stage_word="开端" if current_age==stage_start else "收束" if current_age==stage_end else "推进"
    lines=["## 📍 04｜我现在在哪里？", "", "> [!important] 📍 YOU ARE HERE", f"> **{current_age} 岁 · {current['year']}｜{card_label(number)}**  ", f"> `{start.isoformat()} → {end.isoformat()}`", "", '<table width="100%" style="width:100%; table-layout:fixed;"><tr>', f'<td width="180" align="center"><img src="cards/major_{0 if number==22 else number:02d}.jpg" width="145"><br><b>{card_label(number)}</b></td>', '<td><b>牌面中的象征</b><br>'+"<br>".join(f"{symbol_emoji(n)} <b>{n}</b>：{m}" for n,m in CARD_SYMBOLS[number])+"</td>", "</tr></table>", "", "### 📚 Mary 的年度主题与延伸", "", f"**年度主题：** {ANNUAL_THEMES[number]}", "", f"- **这一年正在练习：** {CARDS[number][2]}", f"- **可以怎样落地：** 把“{SHORT[number][0]}”拆成一个本周能观察、能复盘的小动作。", f"- **需要留意：** {CARDS[number][3]}", f"- **牌面提醒：** {CARD_SYMBOLS[number][0][0]}让抽象主题有了身体和场景；先描述看见什么，再决定它与你有什么关系。", "", "### ⏪ 上一年度 · 📍 当前年度 · ⏩ 下一年度", "", '<table width="100%" style="width:100%; table-layout:fixed;"><tr>']
    for marker,year,card in nearby:
        lines.append(f'<td align="center"><img src="cards/major_{0 if card==22 else card:02d}.jpg" width="92"><br><b>{marker}</b><br>{year} · {card_label(card)}</td>')
    lines.extend(["</tr></table>", "", f"上一张牌留下的动作进入 **{CARDS[number][1]}** 后，当前任务是“{SHORT[number][0]}”；下一张 **{CARDS[nearby[2][2]][1]}** 则提示这段经验会从哪里继续。", "", f"> **阶段坐标：** 当前位于第 {active+1} 段牌序的 **{stage_word}**，这一段覆盖 **{stage_start}～{stage_end} 岁**。你不是站在一张孤立的牌上，而是站在一段正在移动的故事里。", ""])
    return lines


def annual_appendix_markdown() -> list[str]:
    return ["## 📜 08｜方法依据与参考文献", "", "1. **Mary K. Greer, *Tarot for Your Self***：出生牌、性格牌、灵魂牌、隐藏／导师牌、特殊出生牌与年度牌。", "2. **T. Susan Chang, *Tarot Correspondences***：数字 1～10、四元素数字牌、旬区、行星—星座、小阿尔克纳与撒比恩象征。", "3. **Mary K. Greer and Tom Little, *Understanding the Tarot Court***：黄金黎明宫廷牌对应，以及太阳、月亮、上升形象牌。", "", "本报告中的综合段落会把三套资料放在一起阅读，但不会把其中一位作者的体系写成另一位作者的方法。", "", "**牌组与图像：** Rider–Waite–Smith Tarot；图像由 Pamela Colman Smith 创作。新增宫廷牌图来自公开领域 RWS 图像库。彩色图标使用 Twemoji（Twitter 及贡献者，CC BY 4.0）。", "", "---", "", f'<p align="center"><b>{REPORT_SIGNATURE}</b></p>', ""]


def annual_lookup_markdown(rows: list[dict[str, object]], current_age: int, birth: dt.date) -> list[str]:
    full = int(rows[0]["age"]) == 0 and int(rows[-1]["age"]) == 100 and len(rows) == 101
    title = "## 📚 06｜0～100 岁年度牌查询表" if full else f"## 📚 06｜{rows[0]['age']}～{rows[-1]['age']} 岁年度牌查询表"
    lines = [title, "", "> ⭐ 是真实人生节点，📍 是当前所在年份。", ""]
    for band_start, band_end, emoji in AGE_BANDS:
        selected = [r for r in rows if band_start <= int(r["age"]) <= band_end]
        if not selected: continue
        lines.extend([f"### {emoji} {selected[0]['age']}～{selected[-1]['age']} 岁", "", '<table width="100%" style="width:100%; table-layout:fixed;">', '<thead><tr><th width="8%">年龄</th><th width="12%">公历年份</th><th width="18%">完整核算</th><th width="10%">牌面</th><th width="22%">中英文牌名</th><th width="30%">人生节点／备注</th></tr></thead><tbody>'])
        for row in selected:
            age, number = int(row["age"]), int(row["card"]); image_number = 0 if number == 22 else number
            marker = ("⭐" if row["nodes"] else "") + ("📍" if age == current_age else "")
            note = "；".join(str(n) for n in row["nodes"])
            calc = f"{birth.month} + {birth.day} + {row['year']} = {row['total']} → {reduction_text(int(row['total']))}"
            lines.append(f'<tr><td align="center">{age}</td><td align="center">{row["year"]} {marker}</td><td align="center">{calc}</td><td align="center"><img src="cards/major_{image_number:02d}.jpg" width="42"></td><td>{card_label(number)}</td><td>{note}</td></tr>')
        lines.extend(["</tbody></table>", ""])
    return lines


def make_chart(rows: list[dict[str, object]], path: Path, current_age: int | None) -> None:
    """Render a sequence timeline; vertical position never encodes card value."""
    cell_w, cell_h, cols = 150, 115, min(10, max(1, len(rows)))
    grid_rows = (len(rows)+cols-1)//cols; width, height = cols*cell_w+40, grid_rows*cell_h+80
    parts = ['<?xml version="1.0" encoding="UTF-8"?>', f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="#FBF7EE"/>', '<g font-family="Noto Serif SC, serif" fill="#332C36">', svg_text(20,30,f"{rows[0]['age']}～{rows[-1]['age']} 岁牌序时间轴",font_size="18",font_weight="700")]
    for i,row in enumerate(rows):
        x=20+(i%cols)*cell_w; y=50+(i//cols)*cell_h; age=int(row["age"]); number=int(row["card"])
        fill = "#F6E6B5" if current_age == age else ("#EEE8F2" if row["nodes"] else "#FFFDF8")
        parts.extend([f'<rect x="{x}" y="{y}" width="{cell_w-8}" height="{cell_h-10}" rx="7" fill="{fill}" stroke="#956C2C" stroke-width="1"/>', svg_text(x+10,y+24,f"{age} 岁 · {row['year']}",font_size="13",font_weight="700"), svg_text(x+10,y+51,card_label(number),font_size="11"), svg_text(x+10,y+78,SHORT[number][0].split("，")[0],font_size="11",fill="#75627F")])
    parts.extend(['</g>','</svg>']); path.write_text("\n".join(parts),encoding="utf-8")


def build_report(args: argparse.Namespace) -> Path:
    birth = args.birth_date
    if args.age_start < 0 or args.age_end < args.age_start:
        raise ValueError("年龄范围必须满足 0 ≤ age-start ≤ age-end")
    if args.chart_span < 5:
        raise ValueError("chart-span 至少为 5")
    if birth > args.as_of:
        raise ValueError("出生日期不能晚于当前／指定日期")
    for label, value in (("月亮黄经", args.moon_longitude), ("上升黄经", args.rising_longitude)):
        if value is not None and not 0 <= value < 360:
            raise ValueError(f"{label}必须满足 0 ≤ x < 360")

    nodes = parse_nodes(args.node, birth)
    current_age = age_on(args.as_of, birth)
    rows: list[dict[str, object]] = []
    for age in range(args.age_start, args.age_end + 1):
        year = birth.year + age
        total, card = year_card(birth, year)
        rows.append({
            "age": age,
            "year": year,
            "total": total,
            "card": card,
            "nodes": nodes.get(year, []),
        })

    # The chart always begins at age 0, even when the requested table starts later.
    chart_rows: list[dict[str, object]] = []
    for age in range(0, args.age_end + 1):
        year = birth.year + age
        total, card = year_card(birth, year)
        chart_rows.append({"age": age, "year": year, "total": total, "card": card, "nodes": nodes.get(year, [])})

    out_dir = args.output_dir.resolve()
    chart_dir = out_dir / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"年度牌图谱_{birth.isoformat()}_{args.age_start}-{args.age_end}岁.md"
    profile = birth_profile(birth)
    roles, minors = copy_profile_assets(profile, birth, out_dir)
    loop_analysis = analyze_loops(rows, profile, current_age)

    chart_refs: list[tuple[str, str]] = []
    chart_chunks: list[list[dict[str, object]]] = []
    for offset in range(0, len(chart_rows), args.chart_span):
        chunk = chart_rows[offset:offset + args.chart_span]
        filename = f"年度牌走势_{chunk[0]['age']}-{chunk[-1]['age']}岁.svg"
        visible_current = current_age if 0 <= current_age <= args.age_end else None
        make_chart(chunk, chart_dir / filename, visible_current)
        chart_refs.append((filename, f"{chunk[0]['age']}～{chunk[-1]['age']} 岁年度牌走势"))
        chart_chunks.append(chunk)

    subject = args.name.strip() or f"{birth.isoformat()} 出生者"
    title = args.title or f"{subject}｜Personal Tarot Map"
    gender = args.gender.strip() if args.gender else "未提供（不影响计算）"
    current_year = birth.year + current_age
    current_total, current_card = year_card(birth, current_year)
    current = {"age": current_age, "year": current_year, "total": current_total, "card": current_card, "nodes": nodes.get(current_year, [])}
    solar = solar_symbols(birth)
    make_astrology_highlight(solar, chart_dir / "astrology_decan.png")
    make_card_cloud(profile, solar, current_card, out_dir)
    lines = [
        "---",
        f'title: "{title}"',
        f'birth_date: "{birth.isoformat()}"',
        f'gender_context: "{gender}"',
        'system: "Mary K. Greer 年度牌"',
        'deck_numbering: "RWS（VIII 力量，XI 正义）"',
        f'age_range: "{args.age_start}-{args.age_end}"',
        f'generated: "{args.as_of.isoformat()}"',
        "---",
        "",
        "# 🌙 Personal Tarot Map",
        "",
        f"**个人塔罗生命地图｜{subject}**", "",
        "> 本图谱用于象征性自我探索，不替代医疗、法律、财务或心理专业意见。",
        "",
        "> [!note] 🧭 阅读路径",
        "> **🔮 READ｜读我的牌：** 01 → 04，先认识自己的牌，再看当前阶段。  ",
        "> **🗺️ LOOK UP｜查我的地图：** 05 → 08，看终身节奏、查询年度牌并记录复盘。", "",
        *WELCOME_MARKDOWN.splitlines(), "",
    ]
    lines.extend(identity_markdown(profile, args, current))
    lines.extend(special_structure_markdown(profile))
    lines.extend(profile_markdown(profile, roles, minors, args))
    lines.extend(synthesis_markdown(profile, args, current_card))
    lines.extend(current_location_markdown(args, current_age, current, loop_analysis))
    lines.extend([
        "## 🗺️ 05｜我的终身塔罗图谱", "",
        "### 🗺️ 年度牌序时间轴", "",
        f"- 🧮 公式：`出生月 + 出生日 + 目标年份`，本报告为 `{birth.month} + {birth.day} + 目标年份`。",
        "- 归约：将总数各位相加；若仍大于 22，继续相加，保留第一个不大于 22 的结果。",
        "- 牌序：RWS，**VIII 力量、XI 正义、21 世界、22／0 愚人**。",
        f"- 📅 年度周期口径：**{ {'birthday': '生日到下一次生日前', 'calendar': '1 月 1 日至 12 月 31 日', 'both': '生日周期与自然年两种都看'}[args.year_boundary] }**。",
        "- 时间轴固定从 **0 岁**开始；所有卡片处于同一水平层级，牌号不表示吉凶或人生质量。", "",
    ])
    if birth.month == 2 and birth.day == 29:
        lines.append("- 闰日说明：2 月 29 日出生者在非闰年以 2 月 28 日作为个人年切换日。")
    for filename, alt in chart_refs:
        lines.extend([f"![{alt}](charts/{filename})", ""])

    visible_node_rows = [row for row in rows if row["nodes"]]
    lines.extend(["### ⭐ 已知人生节点", ""])
    if visible_node_rows:
        lines.extend(["| 所在个人年 | 周岁 | 节点 | 年度牌 |", "|---:|---:|---|---|"])
        for row in visible_node_rows:
            roman, name, _, _ = CARDS[int(row["card"])]
            for node in row["nodes"]:
                lines.append(f"| {row['year']} | {row['age']} | {node} | {roman} {name} |")
        lines.append("")
    else:
        lines = lines[:-2]

    lines.extend(loop_markdown(rows, loop_analysis, current_age))
    lines.extend(annual_lookup_markdown(rows, current_age, birth))
    lines.extend([
        "## ✍️ 07｜年度复盘",
        "",
        f"> [!tip] 📅 与当前年度牌 {card_label(current_card)} 一起回看", "",
        "```markdown",
        "### ✍️ 年度牌复盘：〔年份／年龄／牌名〕",
        "",
        "- 这一年最明显的主题：",
        "- 我正在结束、维持或开始什么：",
        f"- {CARDS[current_card][1]} 的哪个图像最像我的处境：",
        "- 我使用了这张牌的哪一种力量：",
        "- 哪个部分仍令我不舒服或困惑：",
        "- 下一年度回看时，我希望留下什么可核对的记录：",
        "```",
        "",
    ])
    lines.extend(annual_appendix_markdown())
    if args.format == "pdf":
        return build_pdf(args, rows, chart_chunks, profile, roles, minors, current_age, loop_analysis)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    if args.format == "both":
        pdf_path = build_pdf(args, rows, chart_chunks, profile, roles, minors, current_age, loop_analysis)
        return f"{report_path}\n{pdf_path}"
    return report_path


def _pdf_fonts() -> dict[str, str]:
    """Register embedded Song/Kai faces; headings always use a real bold font file."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    font_dir = ASSET_DIR.parent / "fonts"
    regular = font_dir / "NotoSerifSC-Regular.ttf"
    bold = font_dir / "NotoSerifSC-Bold.ttf"
    if not regular.exists() or not bold.exists():
        raise FileNotFoundError("缺少 PDF 字体资产：NotoSerifSC-Regular.ttf / NotoSerifSC-Bold.ttf")
    kai = next((p for p in (Path(r"C:\Windows\Fonts\simkai.ttf"), Path(r"C:\Windows\Fonts\STKAITI.TTF")) if p.exists()), None)
    if kai is None:
        raise FileNotFoundError("未找到可嵌入的楷体字体（KaiTi / STKaiti）")
    for name, path in (("TarotSong", regular), ("TarotSongBold", bold), ("TarotKai", kai)):
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(path)))
    pdfmetrics.registerFontFamily("TarotSong", normal="TarotSong", bold="TarotSongBold", italic="TarotSong", boldItalic="TarotSongBold")
    # The available Kai face has no authentic bold. Per design spec, Kai headings fall back to real Song Bold.
    pdfmetrics.registerFontFamily("TarotKai", normal="TarotKai", bold="TarotSongBold", italic="TarotKai", boldItalic="TarotSongBold")
    return {"song": "TarotSong", "song_bold": "TarotSongBold", "kai": "TarotKai", "kai_bold": "TarotSongBold"}


def build_pdf(args: argparse.Namespace, rows: list[dict[str, object]], chart_chunks: list[list[dict[str, object]]], profile: dict[str, object], roles: list[tuple[int, str]], minors: list[tuple[str, str]], current_age: int, loop_analysis: dict[str, object]) -> Path:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.graphics.shapes import Circle, Drawing, Line, Polygon, Rect
    from reportlab.platypus import (
        BaseDocTemplate, Frame, Image, KeepTogether, LongTable, NextPageTemplate,
        PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle,
    )

    fonts = _pdf_fonts()
    birth = args.birth_date
    out_dir = args.output_dir.resolve()
    path = out_dir / f"年度牌图谱_{birth.isoformat()}_{args.age_start}-{args.age_end}岁.pdf"
    subject = args.name.strip() or f"{birth.isoformat()} 出生者"
    title = args.title or f"{subject}｜终身年度牌图谱"
    page_landscape = landscape(A4)

    warm = colors.HexColor("#FBF7EE")
    purple = colors.HexColor("#2D2139")
    gold = colors.HexColor("#956C2C")
    muted = colors.HexColor("#75627F")
    header_fill = colors.HexColor("#EEE6D5")
    callout_fill = colors.HexColor("#FAF2DD")
    node_fill = colors.HexColor("#EEE8F2")
    current_fill = colors.HexColor("#F6E6B5")
    ink = colors.HexColor("#332C36")
    faint = colors.HexColor("#E8E0D6")
    white_warm = colors.HexColor("#FFFDF8")

    body = ParagraphStyle("pdf-body", fontName=fonts["song"], fontSize=10.5, leading=17, textColor=ink, spaceAfter=5)
    body_center = ParagraphStyle("pdf-body-center", parent=body, alignment=TA_CENTER)
    small = ParagraphStyle("pdf-small", parent=body, fontSize=8.4, leading=12.5, textColor=muted)
    table_text = ParagraphStyle("pdf-table", fontName=fonts["song"], fontSize=8.5, leading=10.2, textColor=ink)
    table_center = ParagraphStyle("pdf-table-center", parent=table_text, alignment=TA_CENTER)
    table_head = ParagraphStyle("pdf-table-head", fontName=fonts["song_bold"], fontSize=8.7, leading=10.5, textColor=purple, alignment=TA_CENTER)
    cover_en = ParagraphStyle("pdf-cover-en", fontName=fonts["song_bold"], fontSize=10, leading=13, tracking=2, alignment=TA_CENTER, textColor=gold)
    cover_title = ParagraphStyle("pdf-cover-title", fontName=fonts["kai_bold"], fontSize=28, leading=38, alignment=TA_CENTER, textColor=purple, spaceAfter=10)
    cover_meta = ParagraphStyle("pdf-cover-meta", fontName=fonts["song"], fontSize=10.5, leading=17, alignment=TA_CENTER, textColor=muted)
    h1 = ParagraphStyle("pdf-h1", fontName=fonts["kai_bold"], fontSize=20, leading=27, textColor=purple, spaceAfter=12, keepWithNext=True)
    h2 = ParagraphStyle("pdf-h2", fontName=fonts["kai_bold"], fontSize=14.5, leading=20, textColor=gold, spaceBefore=8, spaceAfter=6, keepWithNext=True)
    card_title = ParagraphStyle("pdf-card-title", fontName=fonts["kai_bold"], fontSize=13.5, leading=18, textColor=purple, spaceAfter=5, keepWithNext=True)
    guide = ParagraphStyle("pdf-guide", fontName=fonts["kai"], fontSize=10.8, leading=17, textColor=muted, spaceAfter=7)
    question = ParagraphStyle("pdf-question", fontName=fonts["kai"], fontSize=10.8, leading=17, textColor=purple)
    label = ParagraphStyle("pdf-label", fontName=fonts["kai_bold"], fontSize=10.5, leading=14, textColor=gold, keepWithNext=True)
    preface_body = ParagraphStyle("pdf-preface-body", parent=body, fontSize=9.1, leading=14.2, spaceAfter=3.5)
    special_body = ParagraphStyle("pdf-special-body", parent=body, fontSize=9.7, leading=15.2, spaceAfter=4)
    special_eyebrow = ParagraphStyle("pdf-special-eyebrow", parent=cover_en, fontSize=9, leading=12, tracking=1.5)

    portrait_frame = Frame(17*mm, 15*mm, A4[0]-34*mm, A4[1]-36*mm, id="portrait-frame", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    cover_frame = Frame(22*mm, 22*mm, A4[0]-44*mm, A4[1]-44*mm, id="cover-frame", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    landscape_frame = Frame(9*mm, 12*mm, page_landscape[0]-18*mm, page_landscape[1]-30*mm, id="landscape-frame", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

    def cover_page(canvas, document):
        width, height = A4
        canvas.saveState(); canvas.setFillColor(warm); canvas.rect(0, 0, width, height, fill=1, stroke=0)
        canvas.setStrokeColor(purple); canvas.setLineWidth(.8); canvas.rect(10*mm, 10*mm, width-20*mm, height-20*mm, fill=0, stroke=1)
        canvas.setStrokeColor(gold); canvas.setLineWidth(.3); canvas.rect(12*mm, 12*mm, width-24*mm, height-24*mm, fill=0, stroke=1)
        canvas.setFillColor(gold)
        for x, y in ((15*mm, 15*mm), (width-15*mm, 15*mm), (15*mm, height-15*mm), (width-15*mm, height-15*mm)):
            canvas.circle(x, y, 1.1*mm, fill=1, stroke=0)
        canvas.restoreState()

    def portrait_page(canvas, document):
        width, height = A4
        canvas.saveState(); canvas.setFillColor(warm); canvas.rect(0, 0, width, height, fill=1, stroke=0)
        canvas.setStrokeColor(gold); canvas.setLineWidth(.45); canvas.line(17*mm, height-14*mm, width-17*mm, height-14*mm)
        canvas.setFont(fonts["song"], 8); canvas.setFillColor(muted)
        canvas.drawString(17*mm, height-11*mm, "PERSONAL TAROT MAP")
        canvas.drawRightString(width-17*mm, 8.5*mm, str(document.page))
        canvas.drawString(17*mm, 8.5*mm, "Mary K. Greer｜象征性自我反思")
        canvas.restoreState()

    def landscape_page(label_text: str):
        def draw(canvas, document):
            width, height = page_landscape
            canvas.saveState(); canvas.setFillColor(warm); canvas.rect(0, 0, width, height, fill=1, stroke=0)
            canvas.setStrokeColor(gold); canvas.setLineWidth(.45); canvas.line(9*mm, height-13*mm, width-9*mm, height-13*mm)
            canvas.setFont(fonts["song_bold"], 9); canvas.setFillColor(purple)
            canvas.drawString(9*mm, height-9.5*mm, "06｜0～100 岁年度牌查询表")
            canvas.setFont(fonts["song"], 8); canvas.setFillColor(muted)
            canvas.drawRightString(width-9*mm, height-9.5*mm, label_text)
            canvas.drawString(9*mm, 6.5*mm, "牌序位置用于观察循环，不代表吉凶、强弱或人生质量")
            canvas.drawRightString(width-9*mm, 6.5*mm, str(document.page))
            canvas.restoreState()
        return draw

    doc = BaseDocTemplate(str(path), pagesize=A4, title=title, author="Personal Tarot Map")
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[cover_frame], onPage=cover_page, pagesize=A4),
        PageTemplate(id="portrait", frames=[portrait_frame], onPage=portrait_page, pagesize=A4),
    ])

    annual_chunks = [rows[0:21], rows[21:41], rows[41:61], rows[61:81], rows[81:101]] if len(rows) == 101 and int(rows[0]["age"]) == 0 else [rows[i:i+20] for i in range(0, len(rows), 20)]
    for idx, chunk in enumerate(annual_chunks):
        age_label = f"{chunk[0]['age']}～{chunk[-1]['age']} 岁｜{chunk[0]['year']}～{chunk[-1]['year']}"
        doc.addPageTemplates([PageTemplate(id=f"landscape-{idx}", frames=[landscape_frame], onPage=landscape_page(age_label), pagesize=page_landscape)])

    def section(number: str, name: str) -> Paragraph:
        return Paragraph(f"{number}｜{name}", h1)

    def callout(title_text: str, content: str, style=body, fill=callout_fill):
        box = Table([[Paragraph(f"<b>{html.escape(title_text)}</b>", label)], [Paragraph(content, style)]], colWidths=[A4[0]-34*mm])
        box.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), fill), ("BOX", (0,0), (-1,-1), .45, gold), ("LEFTPADDING", (0,0), (-1,-1), 7), ("RIGHTPADDING", (0,0), (-1,-1), 7), ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 6)]))
        return box

    def card_image(number: int, width_mm: float = 25):
        image_number = 0 if number == 22 else number
        image = Image(str(out_dir/"cards"/f"major_{image_number:02d}.jpg"))
        ratio = image.imageHeight / image.imageWidth
        image.drawWidth = width_mm*mm; image.drawHeight = width_mm*ratio*mm
        return image

    def minor_image(filename: str, width_mm: float = 15):
        image = Image(str(out_dir/"cards"/filename)); ratio = image.imageHeight / image.imageWidth
        image.drawWidth = width_mm*mm; image.drawHeight = width_mm*ratio*mm
        return image

    def asset_image(path_value: Path, width_mm: float):
        image = Image(str(path_value)); ratio = image.imageHeight / image.imageWidth
        image.drawWidth = width_mm*mm; image.drawHeight = width_mm*ratio*mm
        return image

    def emoji_image(kind: str, width_mm: float = 4.5):
        code = SIGN_EMOJI_CODE.get(kind) or {"lion":"1f981", "heart":"1f497", "moon":"1f311", "sun":"2600", "spark":"2728", "warning":"26a0", "leaf":"1f33f", "flower":"1f33a", "water":"1f4a7", "mountain":"26f0", "horse":"1f40e", "crown":"1f451", "target":"1f3af", "compass":"1f9ed", "people":"1f465", "door":"1f6aa"}.get(kind, "2728")
        return asset_image(EMOJI_DIR/f"{code}.png", width_mm)

    def crystal_ball_visual() -> Drawing:
        """A print-safe vector crystal ball used only on triggered special pages."""
        width, height = 176*mm, 34*mm
        drawing = Drawing(width, height)
        cx, cy, radius = width/2, 19*mm, 14*mm
        drawing.add(Circle(cx, cy, radius+3*mm, fillColor=None, strokeColor=colors.HexColor("#E7D7AF"), strokeWidth=.8))
        drawing.add(Circle(cx, cy, radius, fillColor=colors.HexColor("#EEE8F6"), strokeColor=purple, strokeWidth=1.4))
        drawing.add(Circle(cx-4*mm, cy+4*mm, 4.2*mm, fillColor=colors.HexColor("#FFFDF8"), strokeColor=None))
        drawing.add(Circle(cx+5*mm, cy+3*mm, 1.1*mm, fillColor=gold, strokeColor=None))
        drawing.add(Circle(cx-6*mm, cy-3*mm, .8*mm, fillColor=gold, strokeColor=None))
        drawing.add(Line(cx-8*mm, cy+1*mm, cx+8*mm, cy-5*mm, strokeColor=colors.HexColor("#C4A3CF"), strokeWidth=.8))
        star_points = [cx, cy+8*mm, cx+1.4*mm, cy+1.4*mm, cx+7*mm, cy, cx+1.4*mm, cy-1.4*mm, cx, cy-8*mm, cx-1.4*mm, cy-1.4*mm, cx-7*mm, cy, cx-1.4*mm, cy+1.4*mm]
        drawing.add(Polygon(star_points, fillColor=colors.HexColor("#D5B76D"), strokeColor=None))
        drawing.add(Rect(cx-11*mm, 2.5*mm, 22*mm, 4*mm, rx=2*mm, ry=2*mm, fillColor=gold, strokeColor=purple, strokeWidth=.6))
        drawing.add(Rect(cx-15*mm, 0, 30*mm, 3*mm, rx=1.5*mm, ry=1.5*mm, fillColor=colors.HexColor("#6E5878"), strokeColor=None))
        return drawing

    def special_pdf_page() -> list[object]:
        data = special_structure_data(profile)
        if data is None:
            return []
        numbers = tuple(int(v) for v in data["cards"])
        card_grid = Table(
            [[card_image(number, 17) for number in numbers], [Paragraph(f"<b>{card_label(number)}</b>", table_center) for number in numbers]],
            colWidths=[176*mm/len(numbers)]*len(numbers),
        )
        card_grid.setStyle(TableStyle([("ALIGN", (0,0), (-1,-1), "CENTER"), ("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 2), ("BOTTOMPADDING", (0,0), (-1,-1), 2)]))
        elements: list[object] = [
            PageBreak(),
            Paragraph(str(data["eyebrow"]), special_eyebrow),
            Spacer(1, 2*mm),
            Paragraph(str(data["title"]), cover_title),
            crystal_ball_visual(),
            callout("你打开了一页隐藏彩蛋", "只有生日计算实际命中这一结构时，本页才会出现。它是这份生命地图中的少见分支，不代表优越、吉凶或确定命运。", special_body, node_fill),
            Spacer(1, 3*mm),
            callout("计算路径", html.escape(str(data["calculation"])), special_body),
            Spacer(1, 3*mm),
            card_grid,
            Spacer(1, 3*mm),
        ]
        elements.extend(Paragraph(html.escape(str(paragraph)), special_body) for paragraph in data["paragraphs"])
        return elements

    constellation, associated, principle = profile["constellation"]
    chain = " → ".join(str(v) for v in profile["chain"])
    solar = solar_symbols(birth)
    personality, soul = int(profile["personality"]), int(profile["soul"])
    positions = image_positions(args, solar)
    current_year = birth.year + current_age
    current_total, current_card = year_card(birth, current_year)
    current_start, current_end = safe_period(current_year, birth)

    cover_title_text = re.sub(r"^Personal Tarot Map\s*[｜|]\s*", "", title.removeprefix("🌙 "))
    story: list[object] = []
    if args.demo_preface:
        story.extend([
            Spacer(1, 8*mm),
            Paragraph("PERSONAL TAROT MAP", cover_en),
            Spacer(1, 3*mm),
            Paragraph("这套 Skill 可以做什么？", cover_title),
            Paragraph("它可以理解为一套“个人塔罗生命地图生成器”。它不进行随机抽牌占卜，而是根据出生日期和指定年份，计算并整理一个人从 0 岁到 100 岁的塔罗年度牌序列，再结合不同塔罗对应体系，生成一份完整、温暖、可长期查阅的个人报告。", preface_body),
            Paragraph("<b>报告会包含：</b>出生牌、性格牌、灵魂牌及符合规则时的隐藏／导师牌；上一年、当年与下一年的年度牌关系；0～100 岁共 101 行完整牌序；核心牌回归、阶段循环与生命回声；生命灵数、四元素机会牌、生日旬区、命运牌、撒比恩象征，以及已提供星座时的太阳／月亮／上升宫廷形象牌。报告内还留有年度复盘和自选焦点牌的图像对话。", preface_body),
            Paragraph("<b>生成所需：</b>出生日期、年龄范围、输出格式，以及生日周期／自然年／两种都看的年度口径。姓名、真实人生节点和月亮／上升星座可以选填。输出支持 Markdown、PDF 或两者。", preface_body),
            Paragraph("<b>体系分工：</b>Mary K. Greer 负责出生牌、年度牌与太阳／月亮／上升形象牌；T. Susan Chang 负责数字、四元素、旬区、行星—星座、小阿尔克纳与撒比恩；黄金黎明宫廷牌资料用于补充人物的元素配方。不同体系会明确区分，不混成一个绝对结论。", preface_body),
            Paragraph("<b>适合怎样使用：</b>查询今年的年度牌，认识自己的出生牌与灵魂牌，观察核心主题在哪些年份重新出现，或留下一本以后每年都能回来翻阅的个人塔罗象征手册。", preface_body),
            callout("谨慎边界", "不根据性别推断婚育、职业或性格，不捏造人生事件，也不把“命运牌”写成宿命预言。本图谱提供的是象征语言与自我观察问题，不替代医疗、法律、财务或心理专业意见。", preface_body),
            Spacer(1, 3*mm),
            callout("关于本范例", "人物“雾岚”、出生日期、月亮与上升星座，以及全部人生节点均为虚构。生日特意设为会触发 19→10→1 稀有牌组，只用于展示 Skill 的计算、特殊分支与排版，不对应任何真实个人。", preface_body, node_fill),
            NextPageTemplate("cover"),
            PageBreak(),
        ])
    story.extend([Spacer(1, 21*mm), Paragraph("PERSONAL TAROT MAP", cover_en), Spacer(1, 7*mm), Paragraph(html.escape(subject), cover_title), Spacer(1, 1*mm), Paragraph(html.escape(cover_title_text), cover_title), Paragraph(f"出生日期 {birth.isoformat()}　｜　{args.age_start}～{args.age_end} 岁　｜　{ {'birthday':'生日周期','calendar':'自然年','both':'生日周期与自然年'}[args.year_boundary] }", cover_meta), Spacer(1, 13*mm)])
    cover_numbers: list[int] = []
    for number in (*tuple(int(v) for v in profile["core_group"]), *(int(v) for v in profile["hidden"]), int(solar["major"])):
        if number not in cover_numbers:
            cover_numbers.append(number)
        if len(cover_numbers) == 3:
            break
    cover_cards = [[card_image(n, 29) for n in cover_numbers], [Paragraph(f"<b>{card_label(n)}</b>", body_center) for n in cover_numbers]]
    cover_table = Table(cover_cards, colWidths=[(A4[0]-54*mm)/len(cover_numbers)]*len(cover_numbers))
    cover_table.setStyle(TableStyle([("ALIGN", (0,0), (-1,-1), "CENTER"), ("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 3), ("BOTTOMPADDING", (0,0), (-1,-1), 3)]))
    welcome_pdf=[]
    for index,block in enumerate(WELCOME_MARKDOWN.split("\n\n")):
        clean=block.replace(" ✨","").replace("🌙","")
        clean=re.sub(r"\*\*(.+?)\*\*",r"<b>\1</b>",clean)
        if index==0:
            heading_row=Table([[emoji_image("spark",6),Paragraph(clean,h2)]],colWidths=[10*mm,166*mm]); heading_row.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),2)])); welcome_pdf.append(heading_row)
        elif index==len(WELCOME_MARKDOWN.split("\n\n"))-2:
            moon_row=Table([[Paragraph(clean,body),emoji_image("moon",6)]],colWidths=[166*mm,10*mm]); moon_row.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),2)])); welcome_pdf.append(moon_row)
        else:
            welcome_pdf.append(Paragraph(clean,body))
    story.extend([cover_table, Spacer(1, 12*mm), callout("边界说明", "本图谱用于象征性自我探索，不替代医疗、法律、财务或心理专业意见。", small), NextPageTemplate("portrait"), PageBreak(), *welcome_pdf, PageBreak()])

    # 01 | Profile card
    story.extend([section("01", "我的塔罗身份卡"), Paragraph("用一页先看见：哪些牌属于我，以及它们分别负责什么。", guide)])
    profile_rows = [[Paragraph(x, table_head) for x in ("牌位", "对应牌", "主要用途")]]
    if profile["structure"] == "19-10-1":
        profile_rows.append([Paragraph("性格／灵魂牌组", table_text), Paragraph(" → ".join(card_label(int(v)) for v in profile["core_group"]), table_text), Paragraph("创造力、自我认同、变化与表达共同参与", table_text)])
    else:
        profile_rows.extend([[Paragraph("性格牌", table_text), Paragraph(card_label(personality), table_text), Paragraph("较可见的人生课题", table_text)], [Paragraph("灵魂牌", table_text), Paragraph(card_label(soul), table_text), Paragraph("内在目的与长期动力", table_text)]])
    profile_rows.extend([Paragraph("隐藏／导师牌", table_text), Paragraph(card_label(int(v)), table_text), Paragraph("尚待认识与整合的资源", table_text)] for v in profile["hidden"])
    profile_rows.extend([
        [Paragraph("太阳星座牌", table_text), Paragraph(card_label(int(solar["major"])), table_text), Paragraph("自我表达与现实呈现", table_text)],
        [Paragraph("命运牌", table_text), Paragraph(str(solar["destiny"]), table_text), Paragraph("具体情境中的直接反应", table_text)],
        [Paragraph("潜力牌", table_text), Paragraph(str(solar["court"]), table_text), Paragraph("可以逐渐发展的资源", table_text)],
        [Paragraph("当前年度牌", table_text), Paragraph(card_label(current_card), table_text), Paragraph("当前阶段的练习主题", table_text)],
    ])
    for position in positions:
        if position["source"] != "太阳":
            profile_rows.insert(-1, [Paragraph(f"{position['source']}形象牌", table_text), Paragraph(str(position["card"]), table_text), Paragraph(f"{position['role'].split('｜')[1]}；{position['basis']}", table_text)])
    profile_table = Table(profile_rows, colWidths=[38*mm, 62*mm, 76*mm], repeatRows=1)
    profile_table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), header_fill), ("GRID", (0,0), (-1,-1), .35, faint), ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6), ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6)]))
    identity_cards = Table([[card_image(n, 20) for n in cover_numbers], [Paragraph(f"<b>{card_label(n)}</b>", table_center) for n in cover_numbers]], colWidths=[176*mm/len(cover_numbers)]*len(cover_numbers))
    identity_cards.setStyle(TableStyle([("ALIGN", (0,0), (-1,-1), "CENTER"), ("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 3), ("BOTTOMPADDING", (0,0), (-1,-1), 3)]))
    story.extend([profile_table, Spacer(1, 7*mm), callout("完整计算链", f"{birth.month} + {birth.day} + {birth.year} = {profile['total']} → {digit_expression(int(profile['total']))} = {personality}<br/>星群：<b>{constellation}</b>　星群主题：<b>{principle}</b>", body), Spacer(1, 7*mm), Paragraph("核心牌面速览", h2), identity_cards])
    story.extend(special_pdf_page())

    # 02 | Symbolic language
    story.extend([PageBreak(), section("02", "我的个人塔罗象征语言"), Paragraph("Mary 的方法不是给出一次性结论，而是邀请你与这些图像一起生活，并在不同阶段反复观察。", guide)])
    role_map: dict[int, list[str]] = defaultdict(list)
    if profile["structure"] == "19-10-1":
        for value in profile["core_group"]: role_map[int(value)].append("性格／灵魂牌组")
    else:
        role_map[personality].append("性格牌"); role_map[soul].append("灵魂牌")
        for value in profile["hidden"]: role_map[int(value)].append("隐藏／导师牌")
    role_map[int(solar["major"])].append("太阳星座牌")
    for number, card_roles in role_map.items():
        role_text = " × ".join(card_roles)
        summary = Table([[card_image(number, 25), Paragraph(f"<b>{role_text}是什么意思？</b><br/>{'<br/><br/>'.join(ROLE_DEFINITIONS[r] for r in card_roles)}<br/><br/><b>星群主题：</b>{principle}", body)]], colWidths=[36*mm, 140*mm])
        summary.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), white_warm), ("BOX", (0,0), (-1,-1), .45, faint), ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("ALIGN", (0,0), (0,0), "CENTER"), ("LEFTPADDING", (0,0), (-1,-1), 7), ("RIGHTPADDING", (0,0), (-1,-1), 7), ("TOPPADDING", (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 7)]))
        story.extend([Paragraph(f"{card_label(number)}｜{role_text}", card_title), summary, Spacer(1, 3*mm), Paragraph("牌面中的象征", label)])
        symbol_rows=[]
        for name,meaning in CARD_SYMBOLS[number]:
            kind="lion" if "狮" in name else "moon" if "月" in name else "sun" if "太阳" in name else "flower" if "花" in name else "water" if "水" in name else "mountain" if "山" in name else "horse" if "马" in name else "crown" if "王冠" in name else "spark"
            symbol_rows.append([emoji_image(kind),Paragraph(f"<b>{html.escape(name)}</b>：{html.escape(meaning)}",body)])
        symbol_table=Table(symbol_rows,colWidths=[8*mm,168*mm]); symbol_table.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2)])); story.append(symbol_table)
        story.append(Paragraph("牌意解读", label))
        point_rows=[]
        for idx,(_icon,heading,text_value) in enumerate(interpretation_points(number,card_roles)):
            point_rows.append([emoji_image(("leaf","spark","warning","compass")[idx]),Paragraph(f"<b>{heading}：</b>{html.escape(text_value)}",body)])
        point_table=Table(point_rows,colWidths=[8*mm,168*mm]); point_table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),white_warm),("BOX",(0,0),(-1,-1),.35,faint),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)])); story.extend([point_table,Spacer(1,6*mm)])
    number_geometry, number_theme = NUMBER_THEMES[soul]
    number_text="<br/>".join(f"<b>{h}：</b>{m}" for h,m in NUMBER_FULL[soul])
    number_box=Table([[asset_image(out_dir/"cards"/f"number_{soul}.png",28),Paragraph(f"<b>数字图形：</b>{number_geometry}<br/><br/>{number_text}",body)]],colWidths=[40*mm,136*mm]); number_box.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),white_warm),("BOX",(0,0),(-1,-1),.4,faint),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("ALIGN",(0,0),(0,0),"CENTER"),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
    story.extend([Paragraph("生命灵数与机会牌｜数字如何进入四种元素", h2), number_box, Paragraph(f"数字 {soul} 把“{number_theme}”带入行动、情感、思考与现实四个领域。", body)])
    opportunity_cards = [item for item in minors if "命运牌" not in item[1]]
    for offset in range(0, len(opportunity_cards), 4):
        chunk = opportunity_cards[offset:offset+4]
        t = Table([[minor_image(name, 13) for name, _ in chunk], [Paragraph(html.escape(lbl), table_center) for _, lbl in chunk]], colWidths=[176*mm/len(chunk)]*len(chunk))
        t.setStyle(TableStyle([("ALIGN", (0,0), (-1,-1), "CENTER"), ("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 3), ("BOTTOMPADDING", (0,0), (-1,-1), 4)])); story.append(t)
        meaning_cells = []
        for _, lbl in chunk:
            suit,rank,title_name,keywords=opportunity_meta(lbl)
            domain = {"权杖":"火／行动与意志", "圣杯":"水／情感与关系", "宝剑":"风／思考与判断", "星币":"土／现实、身体与实践"}[suit]
            meaning_cells.append(Paragraph(f"<b>{html.escape(lbl)}｜{title_name}</b><br/><b>关键词：</b>{keywords}<br/>{domain}<br/>{OPPORTUNITY_MEANINGS[rank][suit]}", body))
        meanings = Table([meaning_cells], colWidths=[176*mm/len(chunk)]*len(chunk))
        meanings.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), white_warm), ("BOX", (0,0), (-1,-1), .35, faint), ("INNERGRID", (0,0), (-1,-1), .25, faint), ("VALIGN", (0,0), (-1,-1), "TOP"), ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6), ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6)]))
        story.extend([meanings, Spacer(1, 3*mm)])
    story.append(Paragraph("<b>四牌合看：</b>权杖问如何行动，圣杯问如何感受与连接，宝剑问如何理解和决定，星币问如何落实并照顾现实。四张牌共同显示同一生命灵数在四个生活领域里的不同练习。", body))
    destiny_file = next(name for name,label_value in minors if "命运牌" in label_value)
    destiny_rank=int(str(solar["destiny"])[2:]); destiny_suit=str(solar["destiny"])[:2]
    destiny_text = f"生日落在 {solar['sign']}第 {solar['decan']} 旬、约 {solar['degree_interval']}，对应 <b>{solar['destiny']}</b>。占星组合为 <b>{PLANET_SYMBOL[str(solar['ruler'])]} {solar['ruler']} × {solar['sign']}</b>；传统牌名为“{MINOR_TITLES[destiny_rank][destiny_suit]}”。<br/><br/><b>牌面中的象征：</b>{destiny_symbol_text(str(solar['destiny'])).replace('**','')}<br/><br/><b>经典牌意：</b>{OPPORTUNITY_MEANINGS[destiny_rank][destiny_suit]}"
    if solar["sabian"]: destiny_text += f"<br/><br/><b>生日对应的撒比恩象征：</b>{solar['sign']} {solar['degree_interval']}：{solar['sabian']}"
    destiny_box=Table([[minor_image(destiny_file,25),emoji_image(str(solar["sign"]),8),Paragraph(destiny_text,body)]],colWidths=[34*mm,12*mm,130*mm]); destiny_box.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),white_warm),("BOX",(0,0),(-1,-1),.4,faint),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("ALIGN",(0,0),(1,0),"CENTER"),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
    story.extend([Paragraph("命运牌｜生日落入的小阿尔克纳", h2),destiny_box,Spacer(1,4*mm),asset_image(out_dir/"charts"/"astrology_decan.png",105),Paragraph("金色区域是出生旬区，红点是生日的日级近似位置。",small), Paragraph("形象牌｜太阳、月亮与上升的宫廷人物", h2), Paragraph("数字牌更像情境，宫廷牌则像活生生的人物：有气质、习惯、动作和表达方式。", body)])
    for position in positions:
        position_sign=position['sign']
        court_copy=bold_selected_cards(court_portrait(position),[position["card"]],pdf=True)
        court_box=Table([[minor_image(court_asset_name(position["card"]),22),emoji_image(position_sign,7),Paragraph(f"<b>{position['role']}</b><br/>{position_label(position)}<br/>对应 <b>{position['card']}</b>｜元素配方 <b>{position['element']}</b><br/><br/>{court_copy}",body)]],colWidths=[31*mm,11*mm,134*mm]); court_box.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),white_warm),("BOX",(0,0),(-1,-1),.35,faint),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("ALIGN",(0,0),(1,0),"CENTER"),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)])); story.append(court_box)
    if len(positions) < 3: story.append(Paragraph("补充月亮或上升星座，或可靠的月亮／上升黄经后，还可以让另外两位宫廷人物进入这张地图。", guide))
    story.append(callout("焦点牌图像对话", "从报告中任意选择一张牌：我为什么此刻选择它？最先看见哪个人物、颜色、动作或物件？如果它能说话，我想问什么？它让我想起什么？我想把哪项观察带回生活？", question))

    # 03 | Synthesis
    support=f"<b>{CARDS[soul][1]}</b>与<b>{CARDS[int(solar['major'])][1]}</b>共同把“{SHORT[soul][0]}”带向可见表达。"
    tension=f"<b>{CARDS[personality][1]}</b>强调{SHORT[personality][0]}，<b>{solar['destiny']}</b>则把注意力拉回具体情境；两者需要互相校正。"
    conclusion_pdf=formatted_combination(soul,pdf=True)
    story.extend([Spacer(1,8*mm),section("03","把这些牌放在一起"),asset_image(out_dir/"charts"/"personal_card_cloud.png",176),Paragraph(f"<b>我是谁：</b>性格牌 <b>{CARDS[personality][1]}</b> 位于中央，是最常使用、也最需要精炼的生命语言。<br/><b>内在协助：</b>{support}<br/><b>现实互动：</b>{tension}<br/><b>我在哪里：</b>当前年度牌 <b>{CARDS[current_card][1]}</b> 把整组牌带到“{SHORT[current_card][0]}”的现场。<br/><b>我想怎样被看见：</b><b>{solar['court']}</b> 与 <b>{CARDS[int(solar['major'])][1]}</b>补充外在表达，但不抢走性格牌的主位。",body),callout("综合结论",conclusion_pdf+" 重点不是选出一张最好的牌，而是让主轴、辅助与当下课题在同一张桌上说话。",body,node_fill)])

    # 04 | Current location
    nearby = []
    for offset, marker in ((-1, "上一年"), (0, "现在"), (1, "下一年")):
        year = current_year + offset; _, number = year_card(birth, year); nearby.append((marker,year,number))
    current_box = Table([[card_image(current_card,30),Paragraph(f"<b>YOU ARE HERE</b><br/><b>{current_age} 岁 · {current_year}</b><br/><font size=\"18\"><b>{card_label(current_card)}</b></font><br/>{current_start.isoformat()} → {current_end.isoformat()}（生日周期）<br/><br/><b>Mary 年度主题：</b>{ANNUAL_THEMES[current_card]}", body_center)]], colWidths=[44*mm,132*mm])
    current_box.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), current_fill), ("BOX", (0,0), (-1,-1), .7, gold), ("TOPPADDING", (0,0), (-1,-1), 9), ("BOTTOMPADDING", (0,0), (-1,-1), 9)]))
    current_symbols=Table([[emoji_image("spark"),Paragraph(f"<b>{n}</b>：{m}",body)] for n,m in CARD_SYMBOLS[current_card]],colWidths=[8*mm,168*mm]); current_symbols.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2)]))
    neighbor_table=Table([[card_image(c,17) for _,_,c in nearby],[Paragraph(f"<b>{m}</b><br/>{y} · {card_label(c)}",table_center) for m,y,c in nearby]],colWidths=[176*mm/3]*3); neighbor_table.setStyle(TableStyle([("ALIGN",(0,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"TOP"),("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    active=int(loop_analysis["active_stage"]); active_stage=loop_analysis["stages"][active]; stage_start=int(active_stage["start"])+args.age_start; stage_end=int(active_stage["end"])+args.age_start; stage_word="开端" if current_age==stage_start else "收束" if current_age==stage_end else "推进"
    extended=f"<b>这一年正在练习：</b>{CARDS[current_card][2]}<br/><b>可以怎样落地：</b>把“{SHORT[current_card][0]}”拆成一个本周能观察、能复盘的小动作。<br/><b>需要留意：</b>{CARDS[current_card][3]}<br/><b>阶段坐标：</b>第 {active+1} 段牌序的{stage_word}，覆盖 {stage_start}～{stage_end} 岁。"
    story.extend([PageBreak(),section("04","我现在在哪里？"),current_box,Spacer(1,5*mm),Paragraph("牌面中的象征",h2),current_symbols,Paragraph("Mary 的年度主题与延伸",h2),Paragraph(extended,body),Paragraph("上一年度 · 当前年度 · 下一年度",h2),neighbor_table,callout("承接、动作与入口",f"上一张牌留下的经验进入 <b>{CARDS[current_card][1]}</b> 后，当前任务是“{SHORT[current_card][0]}”；下一张 <b>{CARDS[nearby[2][2]][1]}</b> 提示这段经验会从哪里继续。",body,node_fill)])

    # 05 | Lifetime map: timelines, nodes, loops, reset
    story.extend([PageBreak(), section("05", "我的终身塔罗图谱"), Paragraph("以下使用年度牌序时间轴，而不是高低折线。牌号只是序列位置，不代表吉凶、能量强弱或人生质量。", guide), Paragraph("年度牌序时间轴", h2)])
    for chunk_index, chunk in enumerate(chart_chunks):
        if chunk_index == 3:
            story.extend([PageBreak(), Paragraph("年度牌序时间轴（续）", h2)])
        tiles = []
        for row in chunk:
            number = int(row["card"]); age = int(row["age"])
            marker = "当前" if age == current_age else ("节点" if row["nodes"] else "")
            tiles.append(Paragraph(f"<b>{age} 岁</b><br/>{row['year']}<br/><b>{CARDS[number][0]}</b><br/>{CARDS[number][1]}" + (f"<br/><font color=\"#956C2C\">{marker}</font>" if marker else ""), table_center))
        col_count = min(9, len(tiles)); tile_rows = [tiles[i:i+col_count] for i in range(0, len(tiles), col_count)]
        if len(tile_rows[-1]) < col_count: tile_rows[-1].extend([""]*(col_count-len(tile_rows[-1])))
        timeline = Table(tile_rows, colWidths=[176*mm/col_count]*col_count)
        timeline_style = [("GRID", (0,0), (-1,-1), .3, faint), ("BACKGROUND", (0,0), (-1,-1), white_warm), ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5)]
        for r_idx, tile_row in enumerate(tile_rows):
            for c_idx, tile in enumerate(tile_row):
                source_idx = r_idx*col_count+c_idx
                if source_idx < len(chunk):
                    age = int(chunk[source_idx]["age"])
                    if age == current_age: timeline_style.append(("BACKGROUND", (c_idx,r_idx), (c_idx,r_idx), current_fill))
                    elif chunk[source_idx]["nodes"]: timeline_style.append(("BACKGROUND", (c_idx,r_idx), (c_idx,r_idx), node_fill))
        timeline.setStyle(TableStyle(timeline_style)); story.append(KeepTogether([timeline, Spacer(1, 4*mm)]))
    visible_nodes = [row for row in rows if row["nodes"]]
    story.extend([Paragraph("已知人生节点", h2)])
    if visible_nodes:
        node_data = [[Paragraph(x, table_head) for x in ("年份", "周岁", "节点", "年度牌")]]
        for row in visible_nodes:
            for node in row["nodes"]: node_data.append([Paragraph(str(row["year"]), table_center), Paragraph(str(row["age"]), table_center), Paragraph(html.escape(str(node)), table_text), Paragraph(card_label(int(row["card"])), table_text)])
        nt = Table(node_data, colWidths=[25*mm, 18*mm, 84*mm, 49*mm], repeatRows=1)
        nt.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), header_fill), ("BACKGROUND", (0,1), (-1,-1), node_fill), ("GRID", (0,0), (-1,-1), .35, faint), ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5)])); story.append(nt)
    story.extend([Paragraph("生命牌序中的回声", h2), Paragraph("核心牌回归记录同一主题在不同年龄的再出现；当前牌序按 Reset 之间的完整阶段展示。所有图表只表达年龄、顺序与分组。", guide), Paragraph("CORE CARD RETURNS｜核心牌回归", card_title)])
    for item in loop_analysis["core_returns"]:
        number = int(item["card"]); ages = "　·　".join(f"{age} 岁" for age in item["ages"])
        row = Table([[card_image(number, 15), Paragraph(f"<b>{card_label(number)}</b><br/>{ages}<br/>同一主题可能以不同成熟度回来。", body)]], colWidths=[24*mm, 152*mm])
        row.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), white_warm), ("BOX", (0,0), (-1,-1), .35, faint), ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5)])); story.append(row)
    active = int(loop_analysis["active_stage"]); stage = loop_analysis["stages"][active]
    arc_rows = rows[int(stage["start"]):int(stage["end"])+1]
    story.extend([Paragraph("CURRENT ARC｜当前十年牌序", card_title)])
    arc_tiles = [Paragraph(f"<b>{r['age']} 岁</b><br/>{r['year']}<br/>{CARDS[int(r['card'])][1]}<br/><font color=\"#75627F\">{SHORT[int(r['card'])][0].split('，')[0]}</font>", table_center) for r in arc_rows]
    arc_cols = min(5, len(arc_tiles)); arc_grid = [arc_tiles[i:i+arc_cols] for i in range(0,len(arc_tiles),arc_cols)]
    if len(arc_grid[-1]) < arc_cols: arc_grid[-1].extend([Paragraph("",table_center)]*(arc_cols-len(arc_grid[-1])))
    arc_table = Table(arc_grid, colWidths=[176*mm/arc_cols]*arc_cols); arc_table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),white_warm),("GRID",(0,0),(-1,-1),.35,faint),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)])); story.append(arc_table)
    story.extend([Paragraph("RESET｜阶段总览与下一次起点转换", card_title)])
    stage_data = [[Paragraph(x,table_head) for x in ("阶段","年龄区间","起点牌","终点牌")]]
    for index,item in enumerate(loop_analysis["stages"],1):
        first,last=rows[int(item["start"])],rows[int(item["end"])]
        stage_data.append([Paragraph(("当前 · " if index-1==active else "")+str(index),table_center),Paragraph(f"{first['age']}～{last['age']} 岁",table_center),Paragraph(card_label(int(first['card'])),table_text),Paragraph(card_label(int(last['card'])),table_text)])
    stage_table=LongTable(stage_data,colWidths=[24*mm,34*mm,59*mm,59*mm],repeatRows=1); stage_table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),header_fill),("GRID",(0,0),(-1,-1),.3,faint),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)])); story.append(stage_table)

    # 06 | Five landscape lookup pages, continuous page numbers.
    for chunk_index, chunk in enumerate(annual_chunks):
        story.extend([NextPageTemplate(f"landscape-{chunk_index}"), PageBreak()])
        annual = [[Paragraph(x, table_head) for x in ("年龄", "公历年份", "核算过程", "牌面", "年度牌名称", "人生节点／备注")]]
        style_commands = [("BACKGROUND", (0,0), (-1,0), header_fill), ("GRID", (0,0), (-1,-1), .28, faint), ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("ALIGN", (0,0), (3,-1), "CENTER"), ("ALIGN", (4,1), (5,-1), "LEFT"), ("LEFTPADDING", (0,0), (-1,-1), 3), ("RIGHTPADDING", (0,0), (-1,-1), 3), ("TOPPADDING", (0,0), (-1,-1), 1.2), ("BOTTOMPADDING", (0,0), (-1,-1), 1.2)]
        for idx, row in enumerate(chunk, 1):
            number = int(row["card"]); age = int(row["age"]); image_number = 0 if number == 22 else number
            image = Image(str(out_dir/"cards"/f"major_{image_number:02d}.jpg")); image.drawHeight = 7.2*mm; image.drawWidth = 7.2/1.728*mm
            notes = []
            if age == current_age: notes.append("当前")
            if row["nodes"]: notes.append("节点：" + "；".join(html.escape(str(n)) for n in row["nodes"]))
            annual.append([Paragraph(str(age), table_center), Paragraph(str(row["year"]), table_center), Paragraph(f"{birth.month}+{birth.day}+{row['year']}={row['total']}<br/>{reduction_text(int(row['total']))}", table_center), image, Paragraph(f"<b>{CARDS[number][0]}</b>　{CARDS[number][1]} / {ENGLISH[number]}", table_text), Paragraph("<br/>".join(notes) or "", table_text)])
            fill = current_fill if age == current_age else (node_fill if row["nodes"] else (white_warm if idx % 2 else warm))
            style_commands.append(("BACKGROUND", (0,idx), (-1,idx), fill))
            if age and age % 10 == 0: style_commands.append(("LINEABOVE", (0,idx), (-1,idx), .8, gold))
        widths = [22.3*mm, 33.5*mm, 50.2*mm, 27.9*mm, 61.4*mm, 83.7*mm]
        table = Table(annual, colWidths=widths, repeatRows=1)
        table.setStyle(TableStyle(style_commands)); story.append(table)

    # 07 | Printable review worksheet
    story.extend([NextPageTemplate("portrait"), PageBreak(), section("07", "年度复盘"), Paragraph(f"把 {card_label(current_card)} 当作一项可观察的练习。", guide)])
    prompts = ["年份／年龄／年度牌", "这一年最明显的现实主题", "我正在结束、维持或开始什么", f"{CARDS[current_card][1]} 的哪个图像最像我的处境", "我使用了这张牌的哪一种力量", "哪个部分仍令我不舒服或困惑", "下一年度回看时，我希望留下什么可核对的记录"]
    worksheet = []
    for i, prompt in enumerate(prompts):
        worksheet.append([Paragraph(prompt, question)])
        worksheet.append([Spacer(1, 10*mm if i else 5*mm)])
    wt = Table(worksheet, colWidths=[176*mm])
    worksheet_styles = [("LINEBELOW", (0,r), (0,r), .35, faint) for r in range(1, len(worksheet), 2)]
    worksheet_styles += [("TOPPADDING", (0,0), (-1,-1), 3), ("BOTTOMPADDING", (0,0), (-1,-1), 3)]
    wt.setStyle(TableStyle(worksheet_styles)); story.append(wt)

    # 08 | Method basis and sources
    signature_box=Table([[Paragraph(f"<b>{REPORT_SIGNATURE}</b>",body_center)]],colWidths=[120*mm])
    signature_box.setStyle(TableStyle([("LINEABOVE",(0,0),(-1,0),.55,gold),("TEXTCOLOR",(0,0),(-1,-1),purple),("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7)]))
    story.extend([PageBreak(), section("08", "方法依据与参考文献"), Paragraph("三套资料各自负责不同层级；正文中的综合解读不会被包装成其中任何作者的原话。", guide), Paragraph("Mary K. Greer, Tarot for Your Self", h2), Paragraph("用于出生牌、性格牌、灵魂牌、隐藏／导师牌、特殊出生牌、年度牌，以及太阳、月亮、上升的形象牌映射。", body), Paragraph("T. Susan Chang, Tarot Correspondences", h2), Paragraph("用于数字 1～10、四元素数字牌、旬区、行星—星座与小阿尔克纳对应，以及撒比恩象征资料。", body), Paragraph("Mary K. Greer and Tom Little, Understanding the Tarot Court", h2), Paragraph("用于补充宫廷牌的元素配方；不替换 Mary 的太阳、月亮、上升星座映射。", body), Spacer(1,6*mm), Paragraph("牌组与图像", h2), Paragraph("Rider-Waite-Smith Tarot；图像由 Pamela Colman Smith 创作。新增宫廷牌图来自公开领域 RWS 图像库。彩色图标使用 Twemoji（Twitter 及贡献者，CC BY 4.0）。", body), Spacer(1,18*mm), signature_box])

    from reportlab.pdfgen.canvas import Canvas
    class TarotCanvas(Canvas):
        def __init__(self, *canvas_args, **canvas_kwargs):
            canvas_kwargs.setdefault("initialFontName", fonts["song"])
            canvas_kwargs.setdefault("initialFontSize", 10)
            super().__init__(*canvas_args, **canvas_kwargs)
    doc.build(story, canvasmaker=TarotCanvas)
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成 Mary K. Greer 终身年度牌 Markdown 或 PDF 报告")
    parser.add_argument("--birth-date", type=parse_date, required=True, help="出生日期 YYYY-MM-DD")
    parser.add_argument("--node", action="append", default=[], help='人生节点："YYYY=事件" 或 "YYYY-MM-DD=事件"，可重复')
    parser.add_argument("--gender", default="", help="可选性别背景；不参与计算")
    parser.add_argument("--name", default="", help="可选报告称呼／姓名")
    parser.add_argument("--moon-sign", choices=tuple(SUN_MAJOR), default="", help="可选月亮星座")
    parser.add_argument("--rising-sign", choices=tuple(SUN_MAJOR), default="", help="可选上升星座")
    parser.add_argument("--moon-longitude", type=float, default=None, help="可选：已可靠计算的月亮绝对黄经 0≤x<360")
    parser.add_argument("--rising-longitude", type=float, default=None, help="可选：已可靠计算的上升点绝对黄经 0≤x<360")
    parser.add_argument("--year-boundary", choices=("birthday", "calendar", "both"), default="birthday", help="年度周期口径")
    parser.add_argument("--age-start", type=int, default=0)
    parser.add_argument("--age-end", type=int, default=100)
    parser.add_argument("--chart-span", type=int, default=18, help="每张图最多显示的年龄点数；默认 18 以容纳逐点双语标签")
    parser.add_argument("--format", choices=("md", "pdf", "both"), default="md", help="输出格式：md、pdf 或 both")
    parser.add_argument("--as-of", type=parse_date, default=dt.date.today(), help="用于当前年龄标注，默认今天")
    parser.add_argument("--title", default="")
    parser.add_argument("--demo-preface", action="store_true", help="在 PDF 正式封面前加入仅供展示的虚构示例说明页")
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        report = build_report(args)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
        return 2
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
