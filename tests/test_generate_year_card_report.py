import argparse
import datetime as dt
import importlib.util
from pathlib import Path
import re
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "generate_year_card_report.py"
SPEC = importlib.util.spec_from_file_location("tarot_report", SCRIPT)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(mod)


def find_date(number):
    for year in range(1950, 2031):
        for month in range(1, 13):
            for day in range(1, 29):
                value = dt.date(year, month, day)
                if mod.birth_profile(value)["personality"] == number:
                    return value
    raise AssertionError(number)


class CalculationTests(unittest.TestCase):
    def test_standard_and_repeated(self):
        profile = mod.birth_profile(dt.date(2003, 1, 2))
        self.assertEqual((profile["personality"], profile["soul"]), (8, 8))
        self.assertEqual(profile["hidden"], (17,))

    def test_special_19_10_1(self):
        profile = mod.birth_profile(find_date(19))
        self.assertEqual(profile["structure"], "19-10-1")
        self.assertEqual(profile["core_group"], (19, 10, 1))
        self.assertEqual(profile["hidden"], ())

    def test_special_22_0_4(self):
        profile = mod.birth_profile(find_date(22))
        self.assertEqual(profile["structure"], "22-0-4")
        self.assertEqual(profile["core_group"], (22, 4))
        self.assertEqual(profile["hidden"], ())

    def test_all_night_cards_hide_no_mentor(self):
        for number in range(14, 19):
            profile = mod.birth_profile(find_date(number))
            self.assertEqual(profile["structure"], "night")
            self.assertEqual(profile["hidden"], ())

    def test_special_pages_are_strictly_conditional(self):
        standard = mod.birth_profile(dt.date(2003, 1, 2))
        self.assertIsNone(mod.special_structure_data(standard))
        self.assertEqual(mod.special_structure_markdown(standard), [])

        nineteen = mod.special_structure_data(mod.birth_profile(find_date(19)))
        self.assertEqual(nineteen["cards"], (19, 10, 1))
        self.assertIn("共同参与性格与灵魂主题", "".join(nineteen["paragraphs"]))

        twenty_two = mod.special_structure_data(mod.birth_profile(find_date(22)))
        self.assertIn("22 − 22 = 0", twenty_two["calculation"])
        self.assertIn("2 + 2 = 4", twenty_two["calculation"])

        for number in range(14, 19):
            night = mod.special_structure_data(mod.birth_profile(find_date(number)))
            self.assertEqual(night["cards"], (number,))
            self.assertIn(mod.NIGHT_CARD_TRANSITIONS[number], "".join(night["paragraphs"]))

    def test_court_boundaries_use_longitude(self):
        self.assertEqual(mod.court_for_longitude(289.999)[0], "星币皇后")
        self.assertEqual(mod.court_for_longitude(290.0)[0], "宝剑骑士")
        self.assertEqual(mod.court_for_longitude(350.0)[0], "权杖皇后")
        self.assertEqual(mod.court_for_longitude(20.0)[0], "星币骑士")

    def test_sabian_and_decan_for_reference_birth(self):
        solar = mod.solar_symbols(dt.date(2003, 1, 2))
        self.assertEqual(solar["destiny"], "星币3")
        self.assertEqual(solar["ruler"], "火星")
        self.assertIn("自然科学讲座", solar["sabian"])
        self.assertEqual(solar["court"], "星币皇后")

    def test_missing_and_complete_image_positions(self):
        solar = mod.solar_symbols(dt.date(2003, 1, 2))
        missing = argparse.Namespace(moon_longitude=None, rising_longitude=None, moon_sign="", rising_sign="")
        complete = argparse.Namespace(moon_longitude=None, rising_longitude=None, moon_sign="狮子座", rising_sign="水瓶座")
        self.assertEqual(len(mod.image_positions(missing, solar)), 1)
        positions = mod.image_positions(complete, solar)
        self.assertEqual(len(positions), 3)
        self.assertEqual(positions[0]["card"], "星币皇后")
        self.assertEqual(positions[1]["card"], "权杖国王")
        self.assertEqual(positions[2]["card"], "宝剑国王")

    def test_full_life_rows_and_birthday_switch(self):
        birth = dt.date(2003, 1, 2)
        rows = [(age, birth.year + age, mod.year_card(birth, birth.year + age)[1]) for age in range(101)]
        self.assertEqual(len(rows), 101)
        self.assertEqual([r[0] for r in rows], list(range(101)))
        self.assertEqual(mod.age_on(dt.date(2026, 1, 1), birth), 22)
        self.assertEqual(mod.age_on(dt.date(2026, 1, 2), birth), 23)

    def test_markdown_content_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            args = mod.build_parser().parse_args(["--birth-date", "2003-01-02", "--format", "md", "--as-of", "2026-09-06", "--output-dir", temp])
            path = mod.build_report(args)
            text = Path(path).read_text(encoding="utf-8")
            self.assertEqual(len(re.findall(r"^## ", text, re.M)), 8)
            self.assertEqual(len(re.findall(r'<tr><td align="center">\d+</td><td align="center">', text)), 101)
            self.assertIn("性格牌 × 灵魂牌是什么意思？", text)
            self.assertIn("牌面中的象征", text)
            self.assertIn("牌意解读", text)
            self.assertIn("主要功课", text)
            self.assertIn("自然优势", text)
            self.assertIn("容易卡住", text)
            self.assertIn("给你的提醒", text)
            self.assertIn("自然科学讲座", text)
            self.assertIn("CORE CARD RETURNS", text)
            self.assertIn("CURRENT ARC", text)
            self.assertNotIn("Loop 01", text)
            self.assertIn("权杖8｜迅速", text)
            self.assertIn("关键词：迅速・消息・推进", text)
            self.assertIn("火中的八让能量迅速汇聚", text)
            self.assertIn("圣杯8｜怠惰", text)
            self.assertIn("水中的八要求离开", text)
            self.assertIn("宝剑8｜阻滞", text)
            self.assertIn("风中的八呈现被念头", text)
            self.assertIn("星币8｜审慎", text)
            self.assertIn("土中的八把力量放进重复练习", text)
            self.assertIn("四牌合看", text)
            self.assertIn("cards/number_8.png", text)
            self.assertIn("charts/astrology_decan.png", text)
            self.assertIn("cards/court_pents_queen.jpg", text)
            self.assertIn("charts/personal_card_cloud.png", text)
            self.assertIn("Mary 的年度主题与延伸", text)
            self.assertNotIn("focus_card", vars(args))
            for forbidden in ("待选择", "资料待补充", "重要节点 A", "重要节点 B", "命运牌与形象牌"):
                self.assertNotIn(forbidden, text)
            for book in ("Tarot for Your Self", "Tarot Correspondences", "Understanding the Tarot Court"):
                self.assertIn(book, text)
            self.assertTrue(text.rstrip().endswith(f'<p align="center"><b>{mod.REPORT_SIGNATURE}</b></p>'))


if __name__ == "__main__":
    unittest.main()
