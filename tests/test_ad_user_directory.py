import unittest

from services.ad_user_directory import requester_users_params, requester_users_sql


class AdUserDirectoryTest(unittest.TestCase):
    def test_requester_users_query_filters_admin_accounts_and_deduplicates_sources(self):
        sql = requester_users_sql(include_query=True, include_limit=True)
        params = requester_users_params(query="javier", limit=30)

        self.assertIn("NOT LIKE %s ESCAPE", sql)
        self.assertIn("UNION ALL", sql)
        self.assertIn("GROUP BY LOWER(SUBSTRING_INDEX(last_user", sql)
        self.assertEqual(params[:4], ("%\\_adm", "%\\_adm", "%\\_adm", "%\\_adm"))
        self.assertEqual(params[-4:], ("%javier%", "%javier%", "%javier%", 30))


if __name__ == "__main__":
    unittest.main()
