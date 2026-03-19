TIER_LIMITS = {
    'free': {
        'daily_messages': 30,
        'max_tokens':     150,
        'model':          'gpt-4o-mini',
        'tts':            False,
        'image_analyze':  False,
        'image_generate': False,
        'web_search':     False,
        'functions':      False,
    },
    'basic': {
        'daily_messages': 100,
        'max_tokens':     300,
        'model':          'gpt-4o-mini',
        'tts':            True,
        'image_analyze':  True,
        'image_generate': False,
        'web_search':     True,
        'functions':      True,
    },
    'premium': {
        'daily_messages': 500,
        'max_tokens':     600,
        'model':          'gpt-4o',
        'tts':            True,
        'image_analyze':  True,
        'image_generate': True,
        'web_search':     True,
        'functions':      True,
    },
    'pro': {
        'daily_messages': 999999,
        'max_tokens':     1000,
        'model':          'gpt-4o',
        'tts':            True,
        'image_analyze':  True,
        'image_generate': True,
        'web_search':     True,
        'functions':      True,
    },
}

PRICING = {
    'basic':         49.99,
    'premium':      149.99,    # güncellendi
    'premium_year': 999.99,
    'pro':          299.99,
}
