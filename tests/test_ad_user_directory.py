import unittest
from unittest.mock import Mock, patch

from services.ad_user_directory import list_requester_users, requester_users_params, requester_users_sql


class AdUserDirectoryTest(unittest.TestCase):
    def test_requester_users_query_filters_admin_accounts_and_deduplicates_sources(self):
        sql = requester_users_sql(include_query=True, include_limit=True)
        params = requester_users_params(query="javier", limit=30)

        self.assertIn("NOT LIKE %s ESCAPE", sql)
        self.assertIn("UNION ALL", sql)
        self.assertNotIn("FROM tasks", sql)
        self.assertIn("GROUP BY LOWER(SUBSTRING_INDEX(last_user", sql)
        self.assertEqual(params[:3], ("%\\_adm", "%\\_adm", "%\\_adm"))
        self.assertEqual(params[-4:], ("%javier%", "%javier%", "%javier%", 30))

    def test_search_endpoint_skips_database_for_short_queries(self):
        import blueprints.bp_stock as bp_stock

        fake_request = Mock()
        fake_request.args.get.return_value = ""

        with patch.object(bp_stock, "request", fake_request), \
                patch.object(bp_stock, "jsonify", lambda value: value), \
                patch.object(bp_stock, "get_db_connection") as get_db_connection:
            response = bp_stock.search_ad_users()

        self.assertEqual(response, [])
        get_db_connection.assert_not_called()

    def test_requester_users_include_display_label_with_fuero(self):
        class _Rows:
            def fetchall(self):
                return [
                    {
                        "username": "jperez",
                        "real_name": "Juan Perez",
                        "phone": "",
                        "fuero": "Civil",
                    },
                    {
                        "username": "msosa",
                        "real_name": "Maria Sosa",
                        "phone": "",
                        "fuero": "Sin Fuero",
                    },
                ]

        class _Conn:
            def execute(self, _sql, _params):
                return _Rows()

        users = list_requester_users(_Conn(), query="pe", limit=30)

        self.assertEqual(users[0]["display_label"], "Juan Perez (Civil)")
        self.assertEqual(users[1]["display_label"], "Maria Sosa")


if __name__ == "__main__":
    unittest.main()
