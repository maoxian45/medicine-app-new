"""说明书解析模块自动化测试。"""

from services.instruction_parser import (
    build_sample_card,
    clean_ocr_text,
    parse_instruction,
)
from services.sample_medicine_loader import (
    find_best_sample,
)


def test_clean_ocr_text() -> None:
    """应清除多余空格和空行。"""

    raw_text = (
        "  维生素C片  \n"
        "\n"
        "规格：  100mg   \n"
        "用法用量：口服"
    )

    result = clean_ocr_text(raw_text)

    assert result == (
        "维生素C片\n"
        "规格： 100mg\n"
        "用法用量：口服"
    )


def test_parse_complete_ocr_without_fallback() -> None:
    """完整 OCR 文字不应触发样例兜底。"""

    ocr_text = (
        "维生素C片\n"
        "规格：100mg\n"
        "用法用量：口服，一次1片，每日1次，饭后服用。\n"
        "密封保存。\n"
        "有效期36个月。"
    )

    result = parse_instruction(ocr_text)

    assert result["name"] == "维生素C片"
    assert result["spec"] == "100mg"
    assert result["dose"] == "1片"
    assert result["frequency"] == "1次"
    assert result["meal_time"] == "饭后"
    assert result["method"] == "口服"
    assert result["location"] == "密封保存"
    assert result["expiry"] == "36个月"

    assert result["data_source"] == "ocr"
    assert result["used_sample_fallback"] is False
    assert result["sample_id"] == ""
    assert result["fallback_fields"] == []
    assert result["demo_only"] is False


def test_split_contraindications_and_precautions() -> None:
    """应分别识别禁忌和注意事项。"""

    ocr_text = (
        "布洛芬缓释胶囊\n"
        "规格：0.3g\n"
        "用法用量：口服，成人一次1粒，一日2次，早晚服用。\n"
        "对本品过敏者禁用，孕妇及哺乳期妇女慎用。\n"
        "密封，在阴凉干燥处保存。\n"
        "有效期24个月。"
    )

    result = parse_instruction(ocr_text)

    assert "对本品过敏者禁用" in result["contraindications"]
    assert "孕妇及哺乳期妇女慎用" in result["precautions"]

    assert "禁用提示" in result["risks"]
    assert "慎用提示" in result["risks"]
    assert "过敏风险" in result["risks"]

def test_incomplete_ocr_does_not_auto_use_sample() -> None:
    """OCR 内容不完整时，不应自动套用演示样例。"""

    result = parse_instruction(
        "布洛芬缓释胶囊"
    )

    assert result["name"] == "布洛芬缓释胶囊"

    # OCR 原文中没有这些字段，因此保持为空。
    assert result["spec"] == ""
    assert result["dose"] == ""
    assert result["frequency"] == ""
    assert result["method"] == ""

    # OCR 路径不再自动使用样例。
    assert result["data_source"] == "ocr"
    assert result["used_sample_fallback"] is False
    assert result["sample_id"] == ""
    assert result["fallback_fields"] == []
    assert result["demo_only"] is False

    # 缺失字段较多，应被标记为低质量解析。
    assert result["parse_quality"] == "poor"

    assert "spec" in result["missing_fields"]
    assert "dose" in result["missing_fields"]
    assert "frequency" in result["missing_fields"]
    assert "method" in result["missing_fields"]
    assert "expiry_text" in result["missing_fields"]


def test_unrelated_text_has_no_sample_match() -> None:
    """无关文字不应错误匹配任何样例药品。"""

    result = find_best_sample(
        "完全无关的模糊文字"
    )

    assert result is None

    def test_parse_expiry_text() -> None:
        """应同时返回有效期值和有效期原文。"""

    result = parse_instruction(
        "维生素C片\n"
        "规格：100mg\n"
        "用法用量：口服，一次1片，每日1次。\n"
        "有效期：36个月。"
    )

    assert result["expiry"] == "36个月"
    assert result["expiry_text"] == "有效期：36个月"


def test_build_elder_speech_text() -> None:
    """应生成适合老人模式的精简口语播报。"""

    result = parse_instruction(
        "布洛芬缓释胶囊\n"
        "用法用量：口服，一次1粒，每日2次，早晚服用。\n"
        "对本品过敏者禁用。"
    )

    elder_text = result["elder_speech_text"]

    assert isinstance(elder_text, str)
    assert "这是布洛芬缓释胶囊" in elder_text
    assert "一次1粒" in elder_text
    assert "一天2次" in elder_text
    assert "不要使用" in elder_text


def test_build_card_from_sample_id() -> None:
    """应能通过 sample_id 直接生成完整样例卡片。"""

    result = build_sample_card(
        "demo_amoxicillin_capsule"
    )

    assert result is not None
    assert result["name"] == "阿莫西林胶囊"
    assert result["data_source"] == "sample"
    assert result["sample_id"] == "demo_amoxicillin_capsule"
    assert result["used_sample_fallback"] is True
    assert result["demo_only"] is True
    assert result["expiry_text"]
    assert result["elder_speech_text"]


def test_unknown_sample_id_returns_none() -> None:
    """不存在的样例 ID 应返回 None。"""

    result = build_sample_card("not-exist")

    assert result is None


def test_parse_aspirin_instruction_with_ocr_section_noise() -> None:
    """阿司匹林说明书 OCR 错位时，不应把警示语误识别为药名。"""

    ocr_text = (
        "阿司匹林片说明书\n"
        "请仔细阅读说明书并在医师指导下使用\n"
        "警示语：1、对本品过敏者禁用；\n"
        "2、有出血症状的消化道溃疡病或其它活性出血患者、\n"
        "【药品名称】\n"
        "血友病或血小板减少患者及哮喘患者禁用。\n"
        "通用名称：阿司匹林片\n"
        "【规格】50mg\n"
        "【用法用量】每日剂量大致在50-150mg（1-3片），一次或分二次服用。或遵医嘱。\n"
        "【不良反应】\n"
        "【禁忌】\n"
        "和舒张轻度升高或Bun及血清肌酐值轻度增加。\n"
        "每日剂量超过1000mg时，可出现上腹不适、恶心、呕吐、胃痛，以及偶可出现收缩压\n"
        "2、有出血症状的消化道溃疡病或其它活性出血患者、血友病或血小板减少患者及哮喘\n"
        "1、对本品过敏者禁用；\n"
        "【注意事项】\n"
        "1、对水杨酸类药物或非甾体消炎药有过敏史者慎用；\n"
        "患者禁用。\n"
        "【孕妇及哺乳期妇女用药】未进行该项实验且无可靠参考文献\n"
        "2、孕妇尤其是妊娠最后三个月的妇女及哺乳期妇女慎用。\n"
        "【有效期】18个月\n"
        "【贮藏】密封，在干燥处保存。"
    )

    result = parse_instruction(ocr_text)

    assert result["name"] == "阿司匹林片"
    assert result["spec"] == "50mg"
    assert result["dose"] == "50-150mg/日（1-3片）"
    assert result["frequency"] == "1-2次"
    assert result["method"] == "口服"
    assert result["location"] == "密封，在干燥处保存"
    assert result["expiry"] == "18个月"
    assert result["parse_quality"] == "good"

    assert "对本品过敏者禁用" in result["contraindications"]
    assert (
        "有出血症状的消化道溃疡病或其它活性出血患者、"
        "血友病或血小板减少患者及哮喘患者禁用"
    ) in result["contraindications"]
    assert "对水杨酸类药物或非甾体消炎药有过敏史者慎用" in result["precautions"]
    assert "孕妇尤其是妊娠最后三个月的妇女及哺乳期妇女慎用" in result["precautions"]

def test_parse_name_ignores_pinyin_label() -> None:
    """药名不能使用“汉语拼音/英文名称”字段，前端卡片只展示中文药名。"""

    ocr_text = (
        "喉炎丸说明书\n"
        "【药品名称】\n"
        "汉语拼音：Houyan Wan\n"
        "通用名称：喉炎丸\n"
        "英文名称：Houyan Pills\n"
        "【规格】每10丸重1g\n"
        "【用法用量】口服，一次10粒，一日2-3次。\n"
        "【注意事项】运动员慎用；疮肿已溃者切勿敷用。\n"
        "【贮藏】密闭，防潮。"
    )

    result = parse_instruction(ocr_text)

    assert result["name"] == "喉炎丸"
    assert "汉语拼音" not in result["name"]
    assert "Houyan" not in result["name"]


def test_pinyin_only_line_is_not_used_as_medicine_name() -> None:
    """只有拼音行时也不能把拼音字段误识别为药名。"""

    result = parse_instruction(
        "【药品名称】\n"
        "汉语拼音：Houyan Wan\n"
        "【用法用量】口服，一次10粒，一日2-3次。"
    )

    assert result["name"] == "未识别药品"


def test_parse_houyan_malformed_ocr_sections() -> None:
    """喉炎丸 OCR 标题断裂时，也应提取规格和完整注意事项。"""

    ocr_text = (
        "九芝壹\n"
        "喉炎丸说明书\n"
        "孕妇慎服：疮肿已溃者切勿敷用；运动员慎用\n"
        "本品含蟾酥，连续服药时间不宜超过7日\n"
        "【药品名称】\n"
        "汉语拼音：Houyan Wan\n"
        "通用名称：喉炎丸\n"
        "【用法用量】口服，一次10粒：小儿一岁一次1粒，二岁一次2粒，三岁一次3~4粒，\n"
        "格】每100粒重0.3g\n"
        "四至八岁一次5~6粒，九至十五岁一次7~9粒：一日2~3次。外用，凡\n"
        "忌】1.孕妇慎服。\n"
        "【注意事项】1.运动员慎用。\n"
        "2.疮肿已溃者切勿敷用。\n"
        "【贮藏】密闭，防潮。\n"
        "【有效期】36个月"
    )

    result = parse_instruction(ocr_text)

    assert result["name"] == "喉炎丸"
    assert result["spec"] == "每100粒重0.3g"
    assert result["dose"] == "10粒"
    assert result["frequency"] == "2-3次"
    assert result["method"] == "口服、外用"
    assert result["expiry"] == "36个月"
    assert "运动员慎用" in result["precautions"]
    assert "疮肿已溃者切勿敷用" in result["precautions"]
    assert "孕妇慎服" in result["precautions"]
    assert "连续服药时间不宜超过7日" in result["precautions"]


def test_parse_xiaochaihu_malformed_ocr_sections() -> None:
    """小柴胡颗粒 OCR 把禁忌/有效期识别错位时，应清理残缺符号。"""

    ocr_text = (
        "小柴胡颗粒说明书\n"
        "［药品名称］\n"
        "汉语拼音：Xiaochaihu Keli\n"
        "通用名称：小柴胡颗粒\n"
        "［用法用量］开水冲服。一次1-2袋，一日3次。\n"
        "［禁\n"
        "过敏反应、心悸等。\n"
        "［注意事项］\n"
        "忌］对本品及所含成份过敏者禁用。\n"
        "2. 不宜在服药期间同时服用滋补性中药。\n"
        "1.忌烟、酒及辛辣、生冷、油腻食物。\n"
        "3. 风寒表证者不宜使用。\n"
        "4. 高血压、心脏病、肝病、糖尿病、肾病等患者应在医师指导下服用。\n"
        "5. 孕妇、哺乳期妇女、年老体弱者应在医师指导下服用。\n"
        "［有效期136个月。\n"
    )

    result = parse_instruction(ocr_text)

    assert result["name"] == "小柴胡颗粒"
    assert result["dose"] == "1-2袋"
    assert result["frequency"] == "3次"
    assert result["method"] == "开水冲服"
    assert result["expiry"] == "36个月"
    assert "对本品及所含成份过敏者禁用" in result["contraindications"]
    assert all("忌］" not in item for item in result["contraindications"])
    assert "不宜在服药期间同时服用滋补性中药" in result["precautions"]
    assert "忌烟、酒及辛辣、生冷、油腻食物" in result["precautions"]
