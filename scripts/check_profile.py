import json, sys, os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def load_signup_response():
    if os.path.exists('signup_response.json'):
        return json.load(open('signup_response.json', 'r', encoding='utf-8'))
    return None

def main():
    user_id = sys.argv[1] if len(sys.argv) > 1 else None

    if not user_id:
        r = load_signup_response()
        if r:
            user_id = r.get('user_id')

    if not user_id:
        print('NO_USER_ID')
        sys.exit(1)

    res = supabase.table('profiles') \
        .select('*') \
        .eq('id', user_id) \
        .maybe_single() \
        .execute()

    print("DATA:", res.data)
    print("ERROR:", res.error)

if __name__ == '__main__':
    main()
