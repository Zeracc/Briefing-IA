import json, sys, os
from app.services.supabase_client import supabase

def load_signup_response():
    # Try JSON file, then raw txt, else None
    if os.path.exists('signup_response.json'):
        try:
            return json.load(open('signup_response.json', 'r', encoding='utf-8'))
        except Exception as e:
            print('WARN: failed to parse signup_response.json:', e)
    if os.path.exists('signup_response.txt'):
        try:
            txt = open('signup_response.txt', 'r', encoding='utf-8').read()
            try:
                return json.loads(txt)
            except Exception:
                print('WARN: signup_response.txt not JSON, content:\n', txt)
        except Exception as e:
            print('WARN: failed to read signup_response.txt:', e)
    return None


def main():
    # Accept user_id as first CLI arg, else try to read signup_response files
    user_id = None
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    else:
        r = load_signup_response()
        if r:
            user_id = r.get('user_id')

    if not user_id:
        print('NO_USER_ID found. Provide user_id as arg or ensure signup_response.json exists.')
        sys.exit(1)

    print('Querying profiles for user_id:', user_id)
    try:
        res = supabase.table('profiles').select('*').eq('id', user_id).maybe_single().execute()
    except Exception as e:
        print('PROFILES_EXCEPTION (request failed):', repr(e))
        sys.exit(2)

    print('PROFILES_QUERY_REPR:', repr(res))
    try:
        data = res.get('data') if isinstance(res, dict) else getattr(res, 'data', None)
        err = res.get('error') if isinstance(res, dict) else getattr(res, 'error', None)
        print('PROFILES_DATA:', data)
        print('PROFILES_ERROR:', err)
    except Exception as e:
        print('PROFILES_EXCEPTION (parsing):', e)


if __name__ == '__main__':
    main()
