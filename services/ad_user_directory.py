def _is_admin_username_sql(alias):
    return f"LOWER(TRIM({alias})) NOT LIKE %s ESCAPE '\\\\'"


def _admin_username_pattern():
    return "%\\_adm"


PCS_LAST_USER_SQL = "SUBSTRING_INDEX(last_user, '\\\\', -1)"
TASK_SOLICITANTE_SQL = "SUBSTRING_INDEX(solicitante, '\\\\', -1)"
P_LAST_USER_SQL = "SUBSTRING_INDEX(p.last_user, '\\\\', -1)"


def requester_users_sql(include_query=False, include_limit=False):
    query_filter = ""
    if include_query:
        query_filter = """
        AND (
            LOWER(src.username) LIKE %s
            OR LOWER(src.real_name) LIKE %s
            OR LOWER(src.fuero) LIKE %s
        )
        """

    limit_clause = "LIMIT %s" if include_limit else ""

    return f"""
        SELECT
            src.username,
            src.real_name,
            src.phone,
            COALESCE(
                NULLIF(NULLIF(NULLIF(TRIM(src.fuero), ''), 'Sin Fuero'), 'Desconocido'),
                'Sin Fuero'
            ) AS fuero
        FROM (
            SELECT
                LOWER(TRIM(a.username)) AS username,
                COALESCE(NULLIF(TRIM(a.real_name), ''), LOWER(TRIM(a.username))) AS real_name,
                a.phone,
                COALESCE(
                    NULLIF(NULLIF(NULLIF(TRIM(a.fuero), ''), 'Sin Fuero'), 'Desconocido'),
                    pc_user.fuero,
                    task_user.fuero
                ) AS fuero
            FROM ad_users a
            LEFT JOIN (
                SELECT
                    LOWER(SUBSTRING_INDEX(last_user, '\\\\', -1)) AS username,
                    MAX(NULLIF(NULLIF(NULLIF(TRIM(fuero), ''), 'Sin Fuero'), 'Desconocido')) AS fuero
                FROM pcs
                WHERE last_user IS NOT NULL
                  AND TRIM(last_user) != ''
                  AND {_is_admin_username_sql(PCS_LAST_USER_SQL)}
                GROUP BY LOWER({PCS_LAST_USER_SQL})
            ) pc_user ON pc_user.username = LOWER(TRIM(a.username))
            LEFT JOIN (
                SELECT
                    LOWER({TASK_SOLICITANTE_SQL}) AS username,
                    MAX(NULLIF(NULLIF(NULLIF(TRIM(fuero), ''), 'Sin Fuero'), 'Desconocido')) AS fuero
                FROM tasks
                WHERE solicitante IS NOT NULL
                  AND TRIM(solicitante) != ''
                  AND {_is_admin_username_sql(TASK_SOLICITANTE_SQL)}
                GROUP BY LOWER({TASK_SOLICITANTE_SQL})
            ) task_user ON task_user.username = LOWER(TRIM(a.username))
            WHERE {_is_admin_username_sql("a.username")}

            UNION ALL

            SELECT
                LOWER({P_LAST_USER_SQL}) AS username,
                MIN(p.last_user) AS real_name,
                NULL AS phone,
                MAX(NULLIF(NULLIF(NULLIF(TRIM(p.fuero), ''), 'Sin Fuero'), 'Desconocido')) AS fuero
            FROM pcs p
            WHERE p.last_user IS NOT NULL
              AND TRIM(p.last_user) != ''
              AND {_is_admin_username_sql(P_LAST_USER_SQL)}
              AND LOWER({P_LAST_USER_SQL}) NOT IN (
                  SELECT LOWER(TRIM(username)) FROM ad_users
              )
            GROUP BY LOWER({P_LAST_USER_SQL})
        ) src
        WHERE src.username IS NOT NULL
          AND TRIM(src.username) != ''
          {query_filter}
        ORDER BY src.real_name ASC
        {limit_clause}
    """


def requester_users_params(query=None, limit=None):
    params = [
        _admin_username_pattern(),
        _admin_username_pattern(),
        _admin_username_pattern(),
        _admin_username_pattern(),
    ]
    if query:
        like_query = f"%{query.strip().lower()}%"
        params.extend([like_query, like_query, like_query])
    if limit is not None:
        params.append(int(limit))
    return tuple(params)


def list_requester_users(conn, query=None, limit=None):
    clean_query = (query or "").strip().lower()
    rows = conn.execute(
        requester_users_sql(include_query=bool(clean_query), include_limit=limit is not None),
        requester_users_params(query=clean_query or None, limit=limit),
    ).fetchall()
    return [dict(row) for row in rows]
