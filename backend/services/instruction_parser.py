"""说明书 OCR 文字清洗、字段提取和用药卡片生成。"""

from __future__ import annotations

import re

from services.sample_medicine_loader import find_sample_by_id


MEDICINE_SUFFIXES = (
    "缓释胶囊", "肠溶胶囊", "软胶囊", "胶囊", "缓释片", "控释片",
    "肠溶片", "咀嚼片", "分散片", "泡腾片", "片", "颗粒", "口服液",
    "混悬液", "糖浆", "合剂", "丸", "散", "滴眼液", "滴鼻液",
    "滴耳液", "喷雾剂", "气雾剂", "吸入剂", "注射液", "乳膏",
    "软膏", "凝胶", "栓剂", "贴剂",
)

SECTION_TITLES = (
    "药品说明书", "说明书", "药品名称", "通用名称", "商品名称", "英文名称",
    "汉语拼音", "成份", "主要成份", "性状", "功能主治", "适应症", "规格",
    "用法用量", "用法与用量", "不良反应", "禁忌", "禁忌症", "注意事项",
    "孕妇及哺乳期妇女用药", "孕妇用药", "哺乳期妇女用药", "儿童用药",
    "老年用药", "药物相互作用", "药物过量", "临床试验", "药理毒理",
    "药代动力学", "贮藏", "储藏", "储存", "包装", "有效期", "保质期",
    "执行标准", "批准文号", "上市许可持有人", "生产企业",
)

SECTION_TITLE_SET = set(SECTION_TITLES)

SECTION_PATTERN = "|".join(
    re.escape(title)
    for title in sorted(
        SECTION_TITLES,
        key=len,
        reverse=True,
    )
)

RISK_RULES = (
    (
        (
            "禁用",
            "禁止使用",
            "不得使用",
            "禁服",
        ),
        "禁用提示",
    ),
    (
        (
            "慎用",
            "谨慎使用",
        ),
        "慎用提示",
    ),
    (
        (
            "过敏",
            "过敏者",
        ),
        "过敏风险",
    ),
    (
        (
            "孕妇",
            "妊娠",
        ),
        "孕妇用药提示",
    ),
    (
        (
            "哺乳期",
            "哺乳妇女",
        ),
        "哺乳期用药提示",
    ),
    (
        (
            "儿童",
            "小儿",
            "婴儿",
        ),
        "儿童用药提示",
    ),
    (
        (
            "老人",
            "老年人",
        ),
        "老人用药提示",
    ),
    (
        (
            "肝功能",
            "肝损伤",
            "肝病",
        ),
        "肝功能风险",
    ),
    (
        (
            "肾功能",
            "肾损伤",
            "肾病",
        ),
        "肾功能风险",
    ),
    (
        (
            "胃溃疡",
            "消化道溃疡",
        ),
        "胃肠道风险",
    ),
    (
        (
            "重复用药",
            "同类药物",
        ),
        "重复用药风险",
    ),
)

CONTRAINDICATION_KEYWORDS = (
    "禁用",
    "禁止使用",
    "不得使用",
    "严禁",
    "忌用",
    "禁服",
)

PRECAUTION_KEYWORDS = (
    "慎用",
    "慎服",
    "谨慎使用",
    "不宜",
    "不宜超过",
    "切勿",
    "勿",
    "忌烟",
    "忌酒",
    "应在医师指导下",
    "请咨询医师",
    "请咨询药师",
    "避免使用",
    "注意",
    "应去医院就诊",
)

NAME_REJECT_KEYWORDS = (
    "禁用",
    "慎用",
    "患者",
    "过敏",
    "出血",
    "症状",
    "医师",
    "医生",
    "药师",
    "指导",
    "警示",
    "请仔细阅读",
    "说明书",
    "药品名称",
    "通用名称",
    "商品名称",
    "英文名称",
    "汉语拼音",
    "拼音",
    "拉丁名",
    "成份",
    "性状",
    "适应症",
    "规格",
    "用法",
    "用量",
    "不良反应",
    "注意事项",
    "有效期",
    "贮藏",
    "包装",
    "批准文号",
    "生产企业",
    "每片含",
    "每粒含",
    "分子式",
    "分子量",
    "化学",
)

CONTRAINDICATION_CONTEXT_WORDS = (
    "过敏",
    "出血",
    "溃疡",
    "血友病",
    "血小板",
    "哮喘",
    "肝",
    "肾",
    "孕妇",
    "儿童",
    "患者",
    "禁忌",
)

SPECIAL_PRECAUTION_SECTIONS = (
    "孕妇及哺乳期妇女用药",
    "孕妇用药",
    "哺乳期妇女用药",
    "儿童用药",
    "老年用药",
    "药物相互作用",
    "药物过量",
)

FULLWIDTH_DIGITS = str.maketrans(
    "０１２３４５６７８９",
    "0123456789",
)

NUMBER = (
    r"(?:"
    r"[0-9]+/[0-9]+"
    r"|[0-9]+(?:\.[0-9]+)?"
    r"|[一二两三四五六七八九十百半数]+"
    r")"
)

RANGE = (
    r"(?:"
    r"-"
    r"|—"
    r"|–"
    r"|~"
    r"|～"
    r"|至"
    r"|到"
    r")"
)

DOSE_UNIT = (
    r"(?:"
    r"片|粒|袋|包|丸|枚|支|瓶|盒|贴|贴片|"
    r"毫升|ml|mL|ML|"
    r"毫克|mg|MG|"
    r"微克|ug|μg|"
    r"克|g|G|"
    r"滴|喷|揿|勺|匙|茶匙|汤匙|"
    r"单位|IU|U"
    r")"
)

CHILD_WORDS = (
    "小儿",
    "儿童",
    "婴儿",
    "新生儿",
    "幼儿",
)

ADULT_WORDS = (
    "成人",
    "成年人",
    "通常",
    "常用量",
    "一般",
)

CN_COUNT = {
    "一": "1",
    "二": "2",
    "两": "2",
    "三": "3",
    "四": "4",
    "五": "5",
    "六": "6",
    "七": "7",
    "八": "8",
    "九": "9",
    "十": "10",
}

HEADING_RE = re.compile(
    (
        rf"^\s*"
        rf"[【\[［(（]?\s*"
        rf"(?P<title>{SECTION_PATTERN})"
        rf"\s*[】\]］)）]?"
        rf"\s*[:：]?\s*"
        rf"(?P<body>.*)$"
    ),
    re.IGNORECASE,
)

BRACKET_HEADING_RE = re.compile(
    (
        rf"[【\[［]\s*"
        rf"(?:{SECTION_PATTERN})"
        rf"\s*[】\]］]"
        rf"\s*[:：]?"
    ),
    re.IGNORECASE,
)

PLAIN_INLINE_HEADING_RE = re.compile(
    (
        rf"(?:(?<=\n)|(?<=[。；;]))"
        rf"\s*"
        rf"(?:{SECTION_PATTERN})"
        rf"\s*[:：]\s*"
    ),
    re.IGNORECASE,
)

NUMBERED_MARKER = (
    r"(?:"
    r"[（(]\s*[0-9]{1,2}\s*[）)]\s*[、.．:：]?"
    r"|[0-9]{1,2}\s*[）)]"
    r"|[0-9]{1,2}\s*[、.．:：]"
    r"|[①②③④⑤⑥⑦⑧⑨⑩"
    r"⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]"
    r"|[一二三四五六七八九十]+"
    r"\s*[、.．:：]"
    r")"
)

NUMBERED_START_RE = re.compile(
    (
        rf"(?:"
        rf"^"
        rf"|(?<=[\n。；;！？!?])"
        rf")"
        rf"\s*"
        rf"{NUMBERED_MARKER}"
        rf"\s*"
    ),
    re.MULTILINE | re.IGNORECASE,
)


def clean_ocr_text(
    raw_text: str,
) -> str:
    """清理 OCR 空白、全角数字和异常空行。"""

    text = (
        raw_text
        .replace(
            "\r\n",
            "\n",
        )
        .replace(
            "\r",
            "\n",
        )
        .replace(
            "\u00a0",
            " ",
        )
        .replace(
            "\u2007",
            " ",
        )
        .replace(
            "\u202f",
            " ",
        )
        .replace(
            "\u3000",
            " ",
        )
        .translate(
            FULLWIDTH_DIGITS
        )
    )

    lines: list[str] = []

    for line in text.splitlines():
        cleaned = re.sub(
            r"[ \t]+",
            " ",
            line,
        ).strip()

        if cleaned:
            lines.append(cleaned)

    return "\n".join(lines)


def _first_match(
    text: str,
    pattern: str,
) -> str:
    """兼容旧代码：返回正则第一次捕获的内容。"""

    match = re.search(
        pattern,
        text,
        re.IGNORECASE,
    )

    if match is None:
        return ""

    return match.group(1).strip(
        " ：:，,。；;\n"
    )


def _compact(
    value: str,
) -> str:
    """删除字段内部空格并转换全角数字。"""

    return re.sub(
        r"\s+",
        "",
        value,
    ).translate(
        FULLWIDTH_DIGITS
    )


def _normalize_number_text(
    value: str,
) -> str:
    """兼容旧代码：压缩数字字段。"""

    return _compact(value)


def _append_unique(
    items: list[str],
    value: str,
) -> None:
    """追加非空且不重复的字符串。"""

    if (
        value
        and value not in items
    ):
        items.append(value)


def _append_safety_unique(
    items: list[str],
    value: str,
) -> None:
    """追加安全条目，并避免包含关系造成的重复。"""

    cleaned = _clean_item(
        value
    )

    if not cleaned:
        return

    compact = re.sub(
        r"\s+",
        "",
        cleaned,
    )

    for existing in items:
        existing_compact = re.sub(
            r"\s+",
            "",
            existing,
        )

        if compact == existing_compact:
            return

        if (
            len(compact) >= 8
            and compact in existing_compact
        ):
            return

        if (
            len(existing_compact) >= 8
            and existing_compact in compact
        ):
            items.remove(existing)
            break

    items.append(cleaned)


def _insert_heading_breaks(
    text: str,
) -> str:
    """为同一行中的【章节标题】补换行。"""

    return re.sub(
        (
            rf"(?<!\n)"
            rf"(?="
            rf"[【\[［]\s*"
            rf"(?:{SECTION_PATTERN})"
            rf"\s*[】\]］]"
            rf")"
        ),
        "\n",
        text,
        flags=re.IGNORECASE,
    ).lstrip("\n")


def _match_heading(
    line: str,
) -> tuple[str, str] | None:
    """判断一行是否为标准说明书章节。"""

    match = HEADING_RE.match(line)

    if match is None:
        return None

    title = match.group("title")

    if title not in SECTION_TITLE_SET:
        return None

    body = (
        match.group("body")
        or ""
    ).strip()

    return title, body


def _cut_next_heading(
    value: str,
) -> tuple[str, bool]:
    """同一行出现下一个章节时截断。"""

    positions: list[int] = []

    for pattern in (
        BRACKET_HEADING_RE,
        PLAIN_INLINE_HEADING_RE,
    ):
        match = pattern.search(value)

        if match is not None:
            positions.append(
                match.start()
            )

    if not positions:
        return value, False

    cut = min(positions)

    return (
        value[:cut].rstrip(),
        True,
    )


def _extract_section(
    text: str,
    titles: tuple[str, ...],
) -> str:
    """提取指定章节到下一个标准章节之间的正文。"""

    targets = set(titles)
    collecting = False
    collected: list[str] = []

    prepared = _insert_heading_breaks(
        text
    )

    for raw_line in prepared.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        heading = _match_heading(line)

        if heading is not None:
            title, body = heading

            if title in targets:
                collecting = True

                if body:
                    body, stop = (
                        _cut_next_heading(
                            body
                        )
                    )

                    if body:
                        collected.append(body)

                    if stop:
                        break

                continue

            if collecting:
                break

            continue

        if collecting:
            content, stop = (
                _cut_next_heading(
                    line
                )
            )

            if content:
                collected.append(content)

            if stop:
                break

    if collected:
        return "\n".join(
            collected
        ).strip()

    target_pattern = "|".join(
        re.escape(title)
        for title in sorted(
            titles,
            key=len,
            reverse=True,
        )
    )

    fallback = re.compile(
        (
            rf"(?:"
            rf"[【\[［(（]?\s*"
            rf"(?:{target_pattern})"
            rf"\s*[】\]］)）]?"
            rf"\s*[:：]?"
            rf")"
            rf"\s*(.*?)"
            rf"(?="
            rf"[【\[［]\s*"
            rf"(?:{SECTION_PATTERN})"
            rf"\s*[】\]］]"
            rf"|"
            rf"\n\s*"
            rf"(?:{SECTION_PATTERN})"
            rf"\s*[:：]?"
            rf"|$"
            rf")"
        ),
        re.DOTALL | re.IGNORECASE,
    )

    match = fallback.search(text)

    if match is None:
        return ""

    return match.group(1).strip()


def _usage_text(
    text: str,
) -> str:
    """优先返回用法用量章节。"""

    return (
        _extract_section(
            text,
            (
                "用法用量",
                "用法与用量",
            ),
        )
        or text
    )


def _short_section_value(
    text: str,
    titles: tuple[str, ...],
) -> str:
    """提取规格、贮藏、有效期等短字段。"""

    value = _extract_section(
        text,
        titles,
    )

    if not value:
        return ""

    value = re.split(
        r"[\n。；;]",
        value,
        maxsplit=1,
    )[0]

    return _normalise_ocr_value(
        titles[0],
        value,
    )


def _normalise_name_candidate(
    value: str,
) -> str:
    """清理药名候选，避免把章节正文或警示语当成药名。"""

    value = re.sub(
        r"\s+",
        "",
        value,
    ).strip(
        "【】[]［］ ：:，,。；;()（）"
    )

    # OCR 经常把“通用名称/汉语拼音/英文名称”等标签和字段值粘在同一行。
    # 药名候选必须只保留真正的名称，不能把“通用名称：”或“汉语拼音：”带到前端。
    value = re.sub(
        r"^(?:药品名称|通用名称|商品名称|中文名称|名称)[:：]",
        "",
        value,
    )

    # 拼音和英文名不是 App 首页卡片要展示的药名；清掉标签后若只剩英文，后续会被拒绝。
    value = re.sub(
        r"^(?:汉语拼音|拼音|英文名称|英文名|拉丁名)[:：]",
        "",
        value,
    )

    value = re.sub(
        r"(?:说明书|药品说明书)$",
        "",
        value,
    )

    return value.strip(
        "【】[]［］ ：:，,。；;()（）"
    )



def _normalise_ocr_value(
    label: str,
    value: str,
) -> str:
    """清理短字段里常见的 OCR 误识别符号。"""

    value = value.strip(
        " ：:，,。；;【】[]［］()（）"
    )

    if label in (
        "有效期",
        "保质期",
    ):
        compact = re.sub(
            r"\s+",
            "",
            value,
        )

        # 常见 OCR：［有效期］36个月 被识别为 ［有效期136个月。
        # 只在去掉多余的“1”后落入常见有效期时才修正，避免误改真实 120 个月。
        match = re.fullmatch(
            r"1(?P<months>12|18|24|30|36|48|60|72)\s*个月",
            compact,
        )

        if match is not None:
            return f"{match.group('months')}个月"

    return value


def _line_fragment_body(
    line: str,
    fragment: str,
) -> str:
    """提取“格】/忌】/忌］”这类丢失标题前半部分的 OCR 行正文。"""

    match = re.match(
        rf"^\s*{fragment}\s*[】\]］]\s*[:：]?\s*(?P<body>.+)$",
        line,
        re.IGNORECASE,
    )

    if match is None:
        return ""

    return match.group("body").strip()


def _fragment_heading_items(
    text: str,
    fragments: tuple[str, ...],
) -> list[str]:
    """从丢失前半部分的章节标题行里取正文。"""

    result: list[str] = []

    for line in text.splitlines():
        for fragment in fragments:
            body = _line_fragment_body(
                line,
                fragment,
            )

            if body:
                _append_unique(
                    result,
                    body,
                )

    return result


def _keyword_items_from_lines(
    text: str,
    keywords: tuple[str, ...],
) -> list[str]:
    """按行提取安全提示，减少跨章节误拼接。"""

    items: list[str] = []

    for line in text.splitlines():
        if not _contains_any(
            line,
            keywords,
        ):
            continue

        line_for_check = line.strip(
            "【】[]［］ ：:，,。；;"
        )

        # 跳过纯说明性文案，避免“请仔细阅读说明书并在医师指导下使用”进入注意事项。
        if (
            "请仔细阅读说明书" in line
            and not _contains_any(
                line,
                (
                    "慎用",
                    "慎服",
                    "切勿",
                    "不宜",
                    "禁用",
                    "禁止使用",
                ),
            )
        ):
            continue

        # 药物相互作用章节通常不是注意事项卡片的主体，避免把“详情请咨询”重复塞进去。
        if line_for_check.startswith(
            (
                "药物相互作用",
                "如与其他药物同时使用",
                "详情请咨询",
            )
        ):
            continue

        for item in _split_fallback_clauses(
            line
        ):
            _append_unique(
                items,
                item,
            )

    return items


def _looks_like_medicine_name(
    value: str,
    *,
    require_suffix: bool = False,
) -> bool:
    """判断候选是否像药品名。"""

    candidate = _normalise_name_candidate(
        value
    )

    if not 2 <= len(candidate) <= 40:
        return False

    if any(
        keyword in candidate
        for keyword in NAME_REJECT_KEYWORDS
    ):
        return False

    if re.fullmatch(
        r"[A-Za-z0-9 .·\-_/]+",
        candidate,
    ):
        return False

    if candidate in SECTION_TITLE_SET:
        return False

    if any(
        candidate.startswith(title)
        for title in SECTION_TITLES
    ):
        return False

    if require_suffix:
        return candidate.endswith(
            MEDICINE_SUFFIXES
        )

    return True


def _extract_medicine_name(
    text: str,
) -> str:
    """提取通用名称或药品名称。"""

    # 最高优先级：说明书中明确的“通用名称”。
    # 这里刻意不让空白跨行，避免【药品名称】后面的警示语被误当作药名。
    labelled_patterns = (
        r"^\s*(?:[【\[［]\s*药品名称\s*[】\]］]\s*)?[【\[［]?\s*通用名称\s*[】\]］]?\s*[:：]\s*(?P<name>[^\n，,。；;]+)",
        r"^\s*(?:[【\[［]\s*药品名称\s*[】\]］]\s*)?[【\[［]?\s*商品名称\s*[】\]］]?\s*[:：]\s*(?P<name>[^\n，,。；;]+)",
        r"^\s*(?:[【\[［]\s*药品名称\s*[】\]］]\s*)?[【\[［]?\s*中文名称\s*[】\]］]?\s*[:：]\s*(?P<name>[^\n，,。；;]+)",
        r"^\s*[【\[［]?\s*药品名称\s*[】\]］]?\s*[:：]\s*(?P<name>[^\n，,。；;]+)",
    )

    for pattern in labelled_patterns:
        for match in re.finditer(
            pattern,
            text,
            re.IGNORECASE | re.MULTILINE,
        ):
            candidate = _normalise_name_candidate(
                match.group("name")
            )

            if _looks_like_medicine_name(
                candidate,
            ):
                return candidate

    # 标题常见形态：阿司匹林片说明书。
    for line in text.splitlines():
        value = line.strip(
            "【】[]［］ ：:，,。；;"
        )

        if value.endswith("说明书"):
            candidate = _normalise_name_candidate(
                value
            )

            if _looks_like_medicine_name(
                candidate,
                require_suffix=True,
            ):
                return candidate

    # 兜底：找独立药名行，但仍必须像药名，不能是警示语或章节正文。
    for line in text.splitlines():
        candidate = _normalise_name_candidate(
            line
        )

        if _looks_like_medicine_name(
            candidate,
            require_suffix=True,
        ):
            return candidate

    for line in text.splitlines():
        candidate = _normalise_name_candidate(
            line
        )

        if _looks_like_medicine_name(
            candidate,
        ):
            return candidate

    return "未识别药品"

def _candidate_score(
    source: str,
    start: int,
    child_boundary: int | None,
) -> int:
    """成人或通用剂量优先，儿童分年龄剂量降权。"""

    context = source[
        max(
            0,
            start - 40,
        ):start
    ]

    score = 0

    if any(
        word in context
        for word in ADULT_WORDS
    ):
        score += 8

    if any(
        word in context
        for word in (
            *CHILD_WORDS,
            "岁",
            "个月",
            "月龄",
            "体重",
            "每公斤",
            "公斤",
            "kg",
        )
    ):
        score -= 8

    if (
        child_boundary is not None
        and start < child_boundary
    ):
        score += 4

    return score


def _best_match(
    source: str,
    matches: list[re.Match[str]],
) -> re.Match[str] | None:
    """从多个候选中选取成人或通用项。"""

    if not matches:
        return None

    child_positions = [
        source.find(word)
        for word in CHILD_WORDS
        if source.find(word) >= 0
    ]

    child_boundary = (
        min(child_positions)
        if child_positions
        else None
    )

    return sorted(
        matches,
        key=lambda match: (
            -_candidate_score(
                source,
                match.start(),
                child_boundary,
            ),
            match.start(),
        ),
    )[0]


def _normalize_count(
    value: str,
) -> str:
    """将常见中文次数转换为阿拉伯数字。"""

    compact = _compact(value)

    return CN_COUNT.get(
        compact,
        compact,
    )


def _format_dose(
    dose: str,
    equivalent: str = "",
    daily: bool = False,
) -> str:
    """格式化单次用量或每日总剂量。"""

    result = _compact(dose)

    if daily:
        result += "/日"

    if equivalent:
        result += (
            f"（{_compact(equivalent)}）"
        )

    return result


def extract_dose(
    text: str,
) -> str:
    """
    提取单次用量。

    没有单次用量时，提取每日总剂量。
    """

    source = _usage_text(text)

    single_pattern = re.compile(
        (
            rf"(?:一次|每次|单次)"
            rf"\s*"
            rf"(?:剂量|用量)?"
            rf"\s*"
            rf"(?:"
            rf"为|是|约为|约|大约为|服用|使用"
            rf")?"
            rf"\s*"
            rf"(?P<dose>"
            rf"{NUMBER}"
            rf"(?:"
            rf"\s*{RANGE}\s*"
            rf"{NUMBER}"
            rf")?"
            rf"\s*{DOSE_UNIT}"
            rf"(?:半)?"
            rf")"
            rf"(?:"
            rf"\s*[（(]\s*"
            rf"(?P<equivalent>"
            rf"{NUMBER}"
            rf"(?:"
            rf"\s*{RANGE}\s*"
            rf"{NUMBER}"
            rf")?"
            rf"\s*{DOSE_UNIT}"
            rf")"
            rf"\s*[）)]"
            rf")?"
        ),
        re.IGNORECASE,
    )

    best = _best_match(
        source,
        list(
            single_pattern.finditer(
                source
            )
        ),
    )

    if best is not None:
        return _format_dose(
            best.group("dose"),
            best.group("equivalent") or "",
        )

    daily_patterns = (
        re.compile(
            (
                rf"(?:"
                rf"每日|每天|一日|全天|24小时(?:内)?"
                rf")"
                rf"\s*"
                rf"(?:总)?"
                rf"(?:剂量|用量|服用量|给药量)"
                rf"\s*"
                rf"(?:"
                rf"大致|大约|约|一般|通常|建议"
                rf")?"
                rf"\s*"
                rf"(?:"
                rf"为|是|在|控制在|范围为|"
                rf"可为|可达|不超过|不得超过"
                rf")?"
                rf"\s*"
                rf"(?P<dose>"
                rf"{NUMBER}"
                rf"(?:"
                rf"\s*{RANGE}\s*"
                rf"{NUMBER}"
                rf")?"
                rf"\s*{DOSE_UNIT}"
                rf")"
                rf"(?:"
                rf"\s*[（(]\s*"
                rf"(?P<equivalent>"
                rf"{NUMBER}"
                rf"(?:"
                rf"\s*{RANGE}\s*"
                rf"{NUMBER}"
                rf")?"
                rf"\s*{DOSE_UNIT}"
                rf")"
                rf"\s*[）)]"
                rf")?"
            ),
            re.IGNORECASE,
        ),
        re.compile(
            (
                rf"(?:每日|每天|一日)"
                rf"\s*"
                rf"(?:服用|使用|给予)?"
                rf"\s*"
                rf"(?P<dose>"
                rf"{NUMBER}"
                rf"(?:"
                rf"\s*{RANGE}\s*"
                rf"{NUMBER}"
                rf")?"
                rf"\s*{DOSE_UNIT}"
                rf")"
                rf"(?:"
                rf"\s*[（(]\s*"
                rf"(?P<equivalent>"
                rf"{NUMBER}"
                rf"(?:"
                rf"\s*{RANGE}\s*"
                rf"{NUMBER}"
                rf")?"
                rf"\s*{DOSE_UNIT}"
                rf")"
                rf"\s*[）)]"
                rf")?"
            ),
            re.IGNORECASE,
        ),
    )

    for pattern in daily_patterns:
        match = pattern.search(source)

        if match is not None:
            return _format_dose(
                match.group("dose"),
                match.group("equivalent") or "",
                daily=True,
            )

    return ""


def _format_frequency(
    first: str,
    second: str | None = None,
) -> str:
    """格式化单次数或范围次数。"""

    first_value = _normalize_count(first)

    if not second:
        return f"{first_value}次"

    second_value = _normalize_count(second)

    return (
        f"{first_value}-"
        f"{second_value}次"
    )


def extract_frequency(
    text: str,
) -> str:
    """提取每日、分次、间隔、周期和按需频次。"""

    source = _usage_text(text)

    once_or_split_patterns = (
        re.compile(
            (
                rf"(?:一次|1次)"
                rf"\s*"
                rf"(?:顿服|服用|使用)?"
                rf"\s*"
                rf"(?:或|亦可|也可)"
                rf"\s*"
                rf"(?:分(?:为|成)?\s*)?"
                rf"(?P<count>{NUMBER})"
                rf"\s*次"
                rf"(?:服用|使用|给药)?"
            ),
            re.IGNORECASE,
        ),
        re.compile(
            (
                rf"(?:分(?:为|成)?\s*)?"
                rf"(?P<count>{NUMBER})"
                rf"\s*次"
                rf"(?:服用|使用|给药)?"
                rf"\s*"
                rf"(?:或|亦可|也可)"
                rf"\s*"
                rf"(?:一次|1次)"
                rf"(?:顿服|服用|使用)?"
            ),
            re.IGNORECASE,
        ),
    )

    for pattern in once_or_split_patterns:
        match = pattern.search(source)

        if match is not None:
            count = _normalize_count(
                match.group("count")
            )

            if count == "1":
                return "1次"

            return f"1-{count}次"

    daily_pattern = re.compile(
        (
            rf"(?:"
            rf"一日|每日|每天|一天|1日|24小时(?:内)?"
            rf")"
            rf"\s*"
            rf"(?:服用|使用|给药)?"
            rf"\s*"
            rf"(?P<first>{NUMBER})"
            rf"(?:"
            rf"\s*{RANGE}\s*"
            rf"(?P<second>{NUMBER})"
            rf")?"
            rf"\s*次"
        ),
        re.IGNORECASE,
    )

    best = _best_match(
        source,
        list(
            daily_pattern.finditer(
                source
            )
        ),
    )

    if best is not None:
        return _format_frequency(
            best.group("first"),
            best.group("second"),
        )

    if re.search(
        (
            r"(?:每日)?"
            r"\s*早晚\s*"
            r"(?:各)?\s*"
            r"(?:1|一)\s*次"
        ),
        source,
    ):
        return "2次"

    if re.search(
        r"(?:一次|1次)\s*顿服",
        source,
    ):
        return "1次"

    split_match = re.search(
        (
            rf"(?:分(?:为|成)?|分早晚)"
            rf"\s*"
            rf"(?P<first>{NUMBER})"
            rf"(?:"
            rf"\s*{RANGE}\s*"
            rf"(?P<second>{NUMBER})"
            rf")?"
            rf"\s*次"
            rf"(?:服用|使用|给药)?"
        ),
        source,
        re.IGNORECASE,
    )

    if split_match is not None:
        return _format_frequency(
            split_match.group("first"),
            split_match.group("second"),
        )

    interval_match = re.search(
        (
            rf"(?P<value>"
            rf"(?:每隔|每)"
            rf"\s*{NUMBER}"
            rf"(?:"
            rf"\s*{RANGE}\s*"
            rf"{NUMBER}"
            rf")?"
            rf"\s*(?:小时|时)"
            rf"\s*(?:1|一)\s*次"
            rf")"
        ),
        source,
        re.IGNORECASE,
    )

    if interval_match is not None:
        return _compact(
            interval_match.group("value")
        )

    period_match = re.search(
        (
            rf"(?P<value>"
            rf"(?:每周|每月|隔日|隔天)"
            rf"\s*{NUMBER}"
            rf"(?:"
            rf"\s*{RANGE}\s*"
            rf"{NUMBER}"
            rf")?"
            rf"\s*次"
            rf")"
        ),
        source,
        re.IGNORECASE,
    )

    if period_match is not None:
        return _compact(
            period_match.group("value")
        )

    needed_match = re.search(
        (
            r"("
            r"必要时(?:服用|使用)?"
            r"|按需(?:服用|使用)?"
            r"|症状发作时(?:服用|使用)?"
            r")"
        ),
        source,
    )

    if needed_match is None:
        return ""

    return needed_match.group(1)


def extract_method(
    text: str,
) -> str:
    """提取一种或多种给药方式。"""

    source = _usage_text(text)

    methods = (
        "温开水冲服",
        "开水冲服",
        "温水冲服",
        "舌下含服",
        "嚼碎服用",
        "雾化吸入",
        "鼻腔喷雾",
        "静脉滴注",
        "静脉注射",
        "肌内注射",
        "皮下注射",
        "直肠给药",
        "阴道给药",
        "涂于患处",
        "涂敷",
        "涂搽",
        "涂抹",
        "贴敷",
        "滴眼",
        "滴鼻",
        "滴耳",
        "含漱",
        "漱口",
        "冲服",
        "口服",
        "含服",
        "吞服",
        "嚼服",
        "外用",
        "吸入",
        "喷雾",
        "注射",
    )

    occurrences: list[
        tuple[int, int, str]
    ] = []

    for method in sorted(
        methods,
        key=len,
        reverse=True,
    ):
        for match in re.finditer(
            re.escape(method),
            source,
            re.IGNORECASE,
        ):
            start, end = match.span()

            overlaps = any(
                not (
                    end <= old_start
                    or start >= old_end
                )
                for (
                    old_start,
                    old_end,
                    _,
                ) in occurrences
            )

            if not overlaps:
                occurrences.append(
                    (
                        start,
                        end,
                        method,
                    )
                )

    result: list[str] = []

    for _, _, method in sorted(
        occurrences,
        key=lambda item: item[0],
    ):
        _append_unique(
            result,
            method,
        )

    if "外用" in result:
        result = [
            method
            for method in result
            if method not in (
                "涂于患处",
                "涂敷",
                "涂搽",
                "涂抹",
                "贴敷",
            )
        ]

    if not result and re.search(
        r"(?:服用|内服|口服后|口服)",
        source,
    ):
        result.append("口服")

    return "、".join(result)


def _extract_method(
    text: str,
) -> str:
    """兼容旧代码。"""

    return extract_method(text)


def _extract_meal_time(
    text: str,
) -> str:
    """提取饭前、饭后、睡前等时间。"""

    source = _usage_text(text)
    result: list[str] = []

    for word in (
        "晨起",
        "早晚",
        "饭前",
        "餐前",
        "饭后",
        "餐后",
        "睡前",
        "空腹",
        "随餐",
        "餐中",
    ):
        if word in source:
            _append_unique(
                result,
                word,
            )

    return "、".join(result)


def _extract_spec(
    text: str,
) -> str:
    """提取规格。"""

    value = _short_section_value(
        text,
        (
            "规格",
        ),
    )

    if value:
        return value

    for body in _fragment_heading_items(
        text,
        (
            "格",
        ),
    ):
        value = re.split(
            r"[\n。；;]",
            body,
            maxsplit=1,
        )[0].strip(
            " ：:，,。；;【】[]［］()（）"
        )

        if value:
            return value

    return _first_match(
        text,
        (
            r"(?:"
            r"每袋装|每包装|每粒含|每片含|"
            r"每丸重|每粒重|每片重|"
            r"每支装|每瓶装"
            r")"
            r"\s*[:：]?\s*"
            r"([^\n，,。；;]+)"
        ),
    )


def _extract_storage(
    text: str,
) -> str:
    """提取贮藏方式。"""

    value = _short_section_value(
        text,
        (
            "贮藏",
            "储藏",
            "储存",
        ),
    )

    if value:
        return value

    for sentence in re.split(
        r"[。；;\n]",
        text,
    ):
        sentence = sentence.strip(
            " ，,"
        )

        if (
            "保存" in sentence
            and len(sentence) <= 80
        ):
            return sentence

    return ""


def _extract_expiry(
    text: str,
) -> tuple[str, str]:
    """返回有效期值和带标准中文冒号的文本。"""

    for label in (
        "有效期",
        "保质期",
    ):
        value = _short_section_value(
            text,
            (
                label,
            ),
        )

        if value:
            return (
                value,
                f"{label}：{value}",
            )

    match = re.search(
        (
            r"(?:[【\[［]\s*)?"
            r"(?P<label>有效期|保质期)"
            r"\s*(?:[】\]］])?"
            r"\s*[:：]?\s*"
            r"(?P<value>[^\n，,。；;]+)"
        ),
        text,
        re.IGNORECASE,
    )

    if match is None:
        return "", ""

    label = match.group("label")

    value = _normalise_ocr_value(
        label,
        match.group(
            "value"
        ),
    )

    if not value:
        return "", ""

    return (
        value,
        f"{label}：{value}",
    )


def _extract_expiry_text(
    text: str,
) -> str:
    """兼容旧代码。"""

    return _extract_expiry(text)[1]


def _clean_item(
    value: str,
) -> str:
    """清理禁忌或注意事项条目的编号和符号。"""

    value = re.sub(
        r"^[\s】\]］}）)·•●▪■◆◇\-—]+",
        "",
        value.strip(),
    )

    value = re.sub(
        (
            r"^(?:"
            r"禁\s*忌症?"
            r"|禁忌症?"
            r"|(?=忌\s*[】\]］])忌"
            r"|注意事项"
            r")"
            r"\s*[】\]］]?"
            r"\s*[:：]?"
        ),
        "",
        value,
        flags=re.IGNORECASE,
    )

    value = re.sub(
        (
            rf"^\s*"
            rf"{NUMBERED_MARKER}"
            rf"\s*"
        ),
        "",
        value,
        count=1,
        flags=re.IGNORECASE,
    )

    value = re.sub(
        r"^\s*[·•●▪■◆◇\-—]+\s*",
        "",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip(
        " \t\r\n：:，,。；;【】[]［］"
    )


def _split_section_items(
    text: str,
) -> list[str]:
    """拆分有编号或无编号的章节正文。"""

    if not text:
        return []

    text = (
        text
        .replace(
            "\r\n",
            "\n",
        )
        .replace(
            "\r",
            "\n",
        )
        .replace(
            "\u00a0",
            " ",
        )
        .replace(
            "\u3000",
            " ",
        )
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    ).strip()

    markers = list(
        NUMBERED_START_RE.finditer(
            text
        )
    )

    items: list[str] = []

    if markers:
        prefix = _clean_item(
            text[
                :markers[0].start()
            ]
        )

        _append_unique(
            items,
            prefix,
        )

        for index, marker in enumerate(
            markers
        ):
            if index + 1 < len(markers):
                end = markers[
                    index + 1
                ].start()
            else:
                end = len(text)

            item = _clean_item(
                text[
                    marker.end():end
                ]
            )

            _append_unique(
                items,
                item,
            )

        return items

    for paragraph in re.split(
        r"\n+",
        text,
    ):
        for sentence in re.split(
            r"(?<=[。；;！!])",
            paragraph,
        ):
            item = _clean_item(
                sentence
            )

            _append_unique(
                items,
                item,
            )

    return items


def _split_fallback_clauses(
    text: str,
) -> list[str]:
    """无明确章节时按标点拆分。"""

    items: list[str] = []

    for raw_value in re.split(
        (
            r"(?:"
            r"\n+"
            r"|。+"
            r"|；+"
            r"|;{1,}"
            r"|！+"
            r"|!+"
            r"|，+"
            r"|,+"
            r")"
        ),
        text,
    ):
        value = _clean_item(
            raw_value
        )

        if (
            value
            and value not in SECTION_TITLE_SET
        ):
            _append_unique(
                items,
                value,
            )

    return items


def _split_clauses(
    text: str,
) -> list[str]:
    """兼容旧代码。"""

    return _split_fallback_clauses(
        text
    )


def _keyword_items(
    text: str,
    keywords: tuple[str, ...],
) -> list[str]:
    """按关键词兜底提取。"""

    return [
        value
        for value in _split_fallback_clauses(
            text
        )
        if any(
            keyword in value
            for keyword in keywords
        )
    ]


def _split_safety_clauses(
    value: str,
) -> list[str]:
    """把混在一条里的禁忌/注意事项按中文分号拆开。"""

    clauses: list[str] = []

    for clause in re.split(
        r"[；;]+",
        value,
    ):
        for sub_clause in re.split(
            r"(?<=慎服)[:：]|(?<=慎用)[:：]",
            clause,
        ):
            cleaned = _clean_item(
                sub_clause
            )

            if cleaned:
                _append_unique(
                    clauses,
                    cleaned,
                )

    return clauses


def _contains_any(
    value: str,
    keywords: tuple[str, ...],
) -> bool:
    """判断文本是否包含任一关键词。"""

    return any(
        keyword in value
        for keyword in keywords
    )


def _looks_like_contraindication(
    value: str,
    *,
    section_based: bool = False,
) -> bool:
    """判断条目是否像禁忌内容。"""

    if _contains_any(
        value,
        CONTRAINDICATION_KEYWORDS,
    ):
        return True

    if not section_based:
        return False

    if _contains_any(
        value,
        CONTRAINDICATION_CONTEXT_WORDS,
    ):
        return True

    return False


def _complete_contraindication_item(
    value: str,
) -> str:
    """为 OCR 截断的禁忌条目补上缺失的“禁用”语义。"""

    value = _clean_item(value)

    if not value:
        return ""

    if _contains_any(
        value,
        CONTRAINDICATION_KEYWORDS,
    ):
        return value

    if value.endswith("哮喘"):
        return f"{value}患者禁用"

    if value.endswith(("患者", "过敏者")):
        return f"{value}禁用"

    if _contains_any(
        value,
        CONTRAINDICATION_CONTEXT_WORDS,
    ):
        return f"{value}禁用"

    return value


def _filter_contraindications(
    items: list[str],
    *,
    section_based: bool = False,
) -> list[str]:
    """过滤禁忌章节中的噪声，例如 OCR 错位混入的不良反应。"""

    result: list[str] = []

    for item in items:
        for clause in _split_safety_clauses(
            item
        ):
            if not _looks_like_contraindication(
                clause,
                section_based=section_based,
            ):
                continue

            cleaned = _complete_contraindication_item(
                clause
            )

            if 2 <= len(cleaned) <= 160:
                _append_unique(
                    result,
                    cleaned,
                )

    return sorted(
        result,
        key=lambda item: (
            0 if "过敏" in item else 1,
            len(item),
        ),
    )


def _filter_precautions(
    items: list[str],
    *,
    section_based: bool = False,
) -> list[str]:
    """过滤注意事项；章节内条目尽量保留，关键词条目作为补充。"""

    result: list[str] = []

    for item in items:
        for clause in _split_safety_clauses(
            item
        ):
            if _contains_any(
                clause,
                CONTRAINDICATION_KEYWORDS,
            ):
                continue

            if (
                not section_based
                and not _contains_any(
                    clause,
                    PRECAUTION_KEYWORDS,
                )
            ):
                continue

            cleaned = _clean_item(
                clause
            )

            if 2 <= len(cleaned) <= 180:
                _append_safety_unique(
                    result,
                    cleaned,
                )

    return result


def _extract_safety_items(
    text: str,
) -> tuple[list[str], list[str]]:
    """优先按完整章节提取禁忌和注意事项。"""

    contraindication_section = _extract_section(
        text,
        (
            "禁忌",
            "禁忌症",
        ),
    )

    raw_contraindications = _split_section_items(
        contraindication_section
    )

    # OCR 常把“【禁忌】”识别成“忌】/忌］”，单独补一次。
    raw_contraindications.extend(
        _fragment_heading_items(
            text,
            (
                "忌",
            ),
        )
    )

    contraindications = _filter_contraindications(
        raw_contraindications,
        section_based=bool(
            contraindication_section
        ),
    )

    precaution_sections = [
        _extract_section(
            text,
            (
                "注意事项",
            ),
        )
    ]

    for title in SPECIAL_PRECAUTION_SECTIONS:
        section = _extract_section(
            text,
            (
                title,
            ),
        )

        if section:
            precaution_sections.append(
                section
            )

    raw_precautions: list[str] = []

    for section in precaution_sections:
        raw_precautions.extend(
            _split_section_items(
                section
            )
        )

    # “忌】1.孕妇慎服”这类 OCR 残缺行，如果不是禁用语义，也要作为注意事项保留。
    raw_precautions.extend(
        _fragment_heading_items(
            text,
            (
                "忌",
            ),
        )
    )

    has_precaution_section = any(
        bool(section)
        for section in precaution_sections
    )

    precautions = _filter_precautions(
        raw_precautions,
        section_based=has_precaution_section,
    )

    # 章节提取到的注意事项之外，再补充页眉警示语或被 OCR 挪到别处的安全提示。
    extra_precautions = _filter_precautions(
        _keyword_items_from_lines(
            text,
            PRECAUTION_KEYWORDS,
        ),
        section_based=False,
    )

    for item in extra_precautions:
        _append_safety_unique(
            precautions,
            item,
        )

    # 没有明确禁忌时才从全文关键词兜底，避免把注意事项里的“禁止使用”混入禁忌卡。
    if not contraindications:
        contraindications = _filter_contraindications(
            _keyword_items_from_lines(
                text,
                CONTRAINDICATION_KEYWORDS,
            ),
            section_based=False,
        )

    if not precautions:
        precautions = _filter_precautions(
            _keyword_items_from_lines(
                text,
                PRECAUTION_KEYWORDS,
            )
        )

    return (
        contraindications,
        precautions,
    )

def _extract_risks(
    text: str,
) -> list[str]:
    """根据关键词生成风险标签。"""

    return [
        label
        for keywords, label in RISK_RULES
        if any(
            keyword in text
            for keyword in keywords
        )
    ]


def _merge_unique_strings(
    first: object,
    second: object,
) -> list[str]:
    """合并字符串列表并去重。"""

    result: list[str] = []

    for value in (
        first,
        second,
    ):
        if not isinstance(
            value,
            list,
        ):
            continue

        for item in value:
            if isinstance(
                item,
                str,
            ):
                _append_unique(
                    result,
                    item,
                )

    return result


def _build_note(
    contraindications: list[str],
    precautions: list[str],
) -> str:
    """生成卡片安全备注。"""

    parts: list[str] = []

    if contraindications:
        parts.append(
            "禁忌："
            + "；".join(
                contraindications
            )
        )

    if precautions:
        parts.append(
            "注意事项："
            + "；".join(
                precautions
            )
        )

    return "。".join(parts)


def _dose_speech_phrase(
    dose: str,
) -> str:
    """
    普通剂量播报“一次1粒”。

    每日总剂量播报“每日总用量50-150mg”。
    """

    if not dose:
        return ""

    if "/日" in dose:
        daily_dose = dose.replace(
            "/日",
            "",
        )

        return (
            f"每日总用量{daily_dose}"
        )

    return f"一次{dose}"


def _frequency_speech_phrase(
    frequency: str,
    elder_mode: bool = False,
) -> str:
    """根据频次类型生成自然播报文案。"""

    if not frequency:
        return ""

    special_prefixes = (
        "每隔",
        "每周",
        "每月",
        "隔日",
        "隔天",
        "必要时",
        "按需",
        "症状发作时",
    )

    if frequency.startswith(
        special_prefixes
    ):
        return frequency

    prefix = (
        "一天"
        if elder_mode
        else "每日"
    )

    return f"{prefix}{frequency}"


def _build_speech_text(
    card: dict[str, object],
) -> str:
    """生成普通模式语音文本。"""

    parts = [
        (
            f"药品名称，"
            f"{card.get('name', '未识别药品')}。"
        )
    ]

    usage: list[str] = []

    dose_phrase = _dose_speech_phrase(
        str(
            card.get(
                "dose",
                "",
            )
        )
    )

    if dose_phrase:
        usage.append(
            dose_phrase
        )

    frequency_phrase = (
        _frequency_speech_phrase(
            str(
                card.get(
                    "frequency",
                    "",
                )
            ),
            elder_mode=False,
        )
    )

    if frequency_phrase:
        usage.append(
            frequency_phrase
        )

    meal_time = str(
        card.get(
            "meal_time",
            "",
        )
    )

    if meal_time:
        usage.append(
            f"{meal_time}服用"
        )

    method = str(
        card.get(
            "method",
            "",
        )
    )

    if method:
        usage.append(method)

    if usage:
        parts.append(
            "识别到的用法为，"
            + "，".join(
                usage
            )
            + "。"
        )

    contraindications = card.get(
        "contraindications",
        [],
    )

    precautions = card.get(
        "precautions",
        [],
    )

    if (
        isinstance(
            contraindications,
            list,
        )
        and contraindications
    ):
        parts.append(
            "禁忌提示，"
            + "，".join(
                contraindications
            )
            + "。"
        )

    if (
        isinstance(
            precautions,
            list,
        )
        and precautions
    ):
        parts.append(
            "注意事项，"
            + "，".join(
                precautions
            )
            + "。"
        )

    if card.get(
        "used_sample_fallback"
    ):
        parts.append(
            "部分信息来自演示样例，"
            "请务必以药品原说明书和医生指导为准。"
        )
    else:
        parts.append(
            "以上为说明书文字识别结果，"
            "使用前请再次核对原说明书。"
        )

    return "".join(parts)


def _simplify_elder_text(
    text: str,
) -> str:
    """把部分专业术语替换为口语。"""

    replacements = {
        "对本品过敏者": "对这种药过敏的人",
        "禁用": "不要使用",
        "禁止使用": "不要使用",
        "慎用": "使用前先问医生",
        "谨慎使用": "使用前先问医生",
        "医务人员": "医生",
        "应在医师指导下": "请按照医生交代的方法",
        "肝功能异常者": "肝脏不好的人",
        "肾功能异常者": "肾脏不好的人",
        "哺乳期妇女": "正在哺乳的人",
    }

    for old, new in replacements.items():
        text = text.replace(
            old,
            new,
        )

    return text


def _build_elder_speech_text(
    card: dict[str, object],
) -> str:
    """生成老人模式语音文本。"""

    parts = [
        f"这是{card.get('name', '这个药')}。"
    ]

    usage: list[str] = []

    dose_phrase = _dose_speech_phrase(
        str(
            card.get(
                "dose",
                "",
            )
        )
    )

    if dose_phrase:
        usage.append(
            dose_phrase
        )

    frequency_phrase = (
        _frequency_speech_phrase(
            str(
                card.get(
                    "frequency",
                    "",
                )
            ),
            elder_mode=True,
        )
    )

    if frequency_phrase:
        usage.append(
            frequency_phrase
        )

    meal_time = str(
        card.get(
            "meal_time",
            "",
        )
    )

    if meal_time:
        usage.append(
            f"{meal_time}服用"
        )

    method = str(
        card.get(
            "method",
            "",
        )
    )

    if method:
        usage.append(method)

    if usage:
        parts.append(
            "请注意，"
            + "，".join(
                usage
            )
            + "。"
        )

    contraindications = card.get(
        "contraindications",
        [],
    )

    precautions = card.get(
        "precautions",
        [],
    )

    if (
        isinstance(
            contraindications,
            list,
        )
        and contraindications
    ):
        parts.append(
            "安全提醒，"
            + _simplify_elder_text(
                str(
                    contraindications[0]
                )
            )
            + "。"
        )

    if (
        isinstance(
            precautions,
            list,
        )
        and precautions
    ):
        parts.append(
            "还要注意，"
            + _simplify_elder_text(
                str(
                    precautions[0]
                )
            )
            + "。"
        )

    if card.get(
        "used_sample_fallback"
    ):
        parts.append(
            "有些内容来自演示样例，"
            "服药前请核对药盒和说明书。"
        )
    else:
        parts.append(
            "服药前，请再核对药名、"
            "用量和服药时间。"
        )

    return "".join(parts)


def build_sample_card(
    sample_id: str,
) -> dict[str, object] | None:
    """根据样例 ID 生成完整演示卡片。"""

    sample = find_sample_by_id(
        sample_id
    )

    if sample is None:
        return None

    def sample_text(
        field: str,
        default: str = "",
    ) -> str:
        value = sample.get(field)

        if isinstance(value, str):
            return value

        return default

    card: dict[str, object] = {
        "emoji": sample_text(
            "emoji",
            "💊",
        ),
        "name": sample_text(
            "name",
            "未识别药品",
        ),
        "spec": sample_text("spec"),
        "category": sample_text("category"),
        "owner": sample_text("owner"),
        "dose": sample_text("dose"),
        "frequency": sample_text("frequency"),
        "meal_time": sample_text("meal_time"),
        "method": sample_text("method"),
        "location": sample_text("location"),
        "expiry": sample_text("expiry"),
        "expiry_text": sample_text(
            "expiry_text",
            sample_text("expiry"),
        ),
        "stock": sample_text("stock"),
        "status": "待确认（样例模板）",
        "risks": _merge_unique_strings(
            [],
            sample.get("risks"),
        ),
        "contraindications": (
            _merge_unique_strings(
                [],
                sample.get(
                    "contraindications"
                ),
            )
        ),
        "precautions": (
            _merge_unique_strings(
                [],
                sample.get(
                    "precautions"
                ),
            )
        ),
        "note": sample_text("note"),
        "original_text": "",
        "speech_text": sample_text(
            "speech_text"
        ),
        "elder_speech_text": sample_text(
            "elder_speech_text"
        ),
        "needs_confirmation": True,
        "data_source": "sample",
        "used_sample_fallback": True,
        "sample_id": sample_text("id"),
        "fallback_fields": [],
        "parse_quality": "sample",
        "missing_fields": [],
        "demo_only": bool(
            sample.get(
                "demo_only",
                True,
            )
        ),
    }

    card["fallback_fields"] = [
        field
        for field in (
            "name",
            "spec",
            "category",
            "dose",
            "frequency",
            "meal_time",
            "method",
            "location",
            "expiry",
            "risks",
            "contraindications",
            "precautions",
        )
        if card.get(field)
    ]

    return card


def parse_instruction(
    ocr_text: str,
) -> dict[str, object]:
    """把 OCR 原始文字转换为结构化用药卡片。"""

    text = clean_ocr_text(
        ocr_text
    )

    name = _extract_medicine_name(
        text
    )

    dose = extract_dose(
        text
    )

    frequency = extract_frequency(
        text
    )

    method = extract_method(
        text
    )

    meal_time = _extract_meal_time(
        text
    )

    if (
        not frequency
        and "早晚" in meal_time
    ):
        frequency = "2次"

    contraindications, precautions = (
        _extract_safety_items(
            text
        )
    )

    expiry, expiry_text = (
        _extract_expiry(
            text
        )
    )

    card: dict[str, object] = {
        "emoji": "💊",
        "name": name,
        "spec": _extract_spec(
            text
        ),
        "category": "",
        "owner": "",
        "dose": dose,
        "frequency": frequency,
        "meal_time": meal_time,
        "method": method,
        "location": _extract_storage(
            text
        ),
        "expiry": expiry,
        "expiry_text": expiry_text,
        "stock": "",
        "status": (
            "待确认"
            if name != "未识别药品"
            else "识别不完整"
        ),
        "risks": _extract_risks(
            "\n".join(
                contraindications + precautions
            )
            or text
        ),
        "contraindications": (
            contraindications
        ),
        "precautions": precautions,
        "note": _build_note(
            contraindications,
            precautions,
        ),
        "original_text": text,
        "needs_confirmation": True,
    }

    core_fields = (
        "name",
        "spec",
        "dose",
        "frequency",
        "method",
        "expiry_text",
    )

    missing_fields = [
        field
        for field in core_fields
        if (
            not card.get(field)
            or (
                field == "name"
                and card.get(field)
                == "未识别药品"
            )
        )
    ]

    card.update(
        {
            "data_source": "ocr",
            "used_sample_fallback": False,
            "sample_id": "",
            "fallback_fields": [],
            "missing_fields": missing_fields,
            "demo_only": False,
        }
    )

    if len(missing_fields) >= 4:
        card["parse_quality"] = "poor"
        card["status"] = "识别不完整"

    elif missing_fields:
        card["parse_quality"] = "partial"
        card["status"] = "待确认"

    else:
        card["parse_quality"] = "good"
        card["status"] = "待确认"

    card["speech_text"] = (
        _build_speech_text(
            card
        )
    )

    card["elder_speech_text"] = (
        _build_elder_speech_text(
            card
        )
    )

    return card