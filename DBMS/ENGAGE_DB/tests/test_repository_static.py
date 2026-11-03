import pathlib
import re
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]

class TestRepositoryStatic(unittest.TestCase):
    def test_required_submission_files(self):
        for file in ["README.md", "src/app.py", "src/postgres_schema.sql", "src/seed.py", "database/schema.sql", "database/sample_data.sql", "database/queries.sql", "report/DBMS_Project_Report.pdf", "presentation/DBMS_Project_Presentation.pptx", "submission/BACSE202_ENGAGE_DB_Submission.docx"]:
            self.assertTrue((ROOT/file).is_file(), file)

    def test_no_secret_config_in_package(self):
        self.assertFalse((ROOT/"src"/".env").exists())
        self.assertFalse((ROOT/"src"/".venv").exists())
        self.assertTrue((ROOT/"src"/".env.example").exists())

    def test_source_has_five_feature_endpoints(self):
        source=(ROOT/"src"/"app.py").read_text(encoding="utf-8")
        paths=["/api/post", "/api/post/<post_id>/like", "/api/post/<post_id>/save", "/api/post/<post_id>/comment", "/api/follow/<target_id>"]
        for path in paths:
            self.assertIn(path,source)

    def test_15_table_sample_inserts(self):
        text=(ROOT/"database"/"sample_data.sql").read_text(encoding="utf-8")
        cmds=re.findall(r"(?im)^INSERT INTO (\w+)",text)
        self.assertEqual(len(cmds),272)
        self.assertEqual(len(set(x.lower() for x in cmds)),15)

    def test_readme_embeds_existing_real_screenshots(self):
        readme=(ROOT/"README.md").read_text(encoding="utf-8")
        for name in ["learning_profile_budget_20.png","learning_profile_budget_2000000.png"]:
            self.assertIn("![", readme)
            self.assertIn("screenshots/"+name,readme)
            self.assertTrue((ROOT/"screenshots"/name).is_file())

if __name__=="__main__":unittest.main()
