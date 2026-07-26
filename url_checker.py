import re
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from util import safe_execute

DATE_REGEX = re.compile(r'^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$')

class URLChecker:
    @staticmethod
    def validate_url(url_str, configured_params):
        """
        Validates the URL string against rules and returns structured validation results.
        """
        empty_result = {
            "is_valid": True,
            "date_valid": True,
            "date_str": None,
            "warnings": [],
            "parsed_params": []
        }

        if not url_str or not url_str.strip():
            return empty_result

        parsed = safe_execute(urlparse, url_str.strip(), error_title="解析エラー", error_message="URLの解析に失敗しました。", default=None)
        if not parsed:
            return {
                "is_valid": False,
                "date_valid": False,
                "date_str": None,
                "warnings": ["URLの解析に失敗しました。"],
                "parsed_params": []
            }

        warnings = []
        date_valid = False
        date_str = None

        # Check path for date at the bottom
        path = parsed.path.rstrip('/')
        if not path:
            warnings.append("警告: URLにパスが存在しないため、日付を確認できません。")
        else:
            segments = path.split('/')
            last_segment = segments[-1] if segments else ""
            date_str = last_segment
            if DATE_REGEX.match(last_segment):
                date_valid = True
            else:
                warnings.append(f"警告: URLの最下層（'{last_segment}'）が日付(YYYY-MM-DD)形式ではありません。")

        # Parse query parameters
        query_list = safe_execute(parse_qsl, parsed.query, error_title="解析エラー", error_message="クエリパラメータの解析に失敗しました。", default=[(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)], keep_blank_values=True)

        parsed_params = []
        for key, value in query_list:
            valid_var = key in configured_params
            valid_val = False

            if valid_var:
                allowed_values = configured_params[key]
                if not allowed_values or value in allowed_values:
                    valid_val = True
                else:
                    warnings.append(f"警告: パラメータ '{key}' の値 '{value}' は設定された許可値に含まれていません（誤字・未登録の可能性があります）。")
            else:
                warnings.append(f"警告: 未登録のパラメータ名 '{key}' が含まれています。")

            parsed_params.append({
                "name": key,
                "value": value,
                "valid_var": valid_var,
                "valid_val": valid_val
            })

        is_valid = date_valid and not any("警告" in w for w in warnings)

        return {
            "is_valid": is_valid,
            "date_valid": date_valid,
            "date_str": date_str,
            "warnings": warnings,
            "parsed_params": parsed_params,
            "parsed_url_obj": parsed,
            "query_list": query_list
        }

    @staticmethod
    def update_query_param(url_str, param_name, new_value):
        def _update():
            parsed = urlparse(url_str.strip())
            query_list = parse_qsl(parsed.query, keep_blank_values=True)
            
            updated = False
            new_query_list = []
            for k, v in query_list:
                if k == param_name:
                    new_query_list.append((k, new_value))
                    updated = True
                else:
                    new_query_list.append((k, v))
            
            if not updated:
                new_query_list.append((param_name, new_value))

            new_query = urlencode(new_query_list)
            return urlunparse(parsed._replace(query=new_query))

        return safe_execute(_update, error_message=None, default=url_str)

    @staticmethod
    def update_query_param_name(url_str, old_param_name, new_param_name):
        def _rename():
            parsed = urlparse(url_str.strip())
            query_list = parse_qsl(parsed.query, keep_blank_values=True)
            
            new_query_list = []
            for k, v in query_list:
                if k == old_param_name:
                    new_query_list.append((new_param_name, v))
                else:
                    new_query_list.append((k, v))

            new_query = urlencode(new_query_list)
            return urlunparse(parsed._replace(query=new_query))

        return safe_execute(_rename, error_message=None, default=url_str)

    @staticmethod
    def remove_query_param(url_str, param_name):
        def _remove():
            parsed = urlparse(url_str.strip())
            query_list = parse_qsl(parsed.query, keep_blank_values=True)
            
            new_query_list = [(k, v) for k, v in query_list if k != param_name]
            new_query = urlencode(new_query_list)
            return urlunparse(parsed._replace(query=new_query))

        return safe_execute(_remove, error_message=None, default=url_str)
