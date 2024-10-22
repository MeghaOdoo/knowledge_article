{
    "name": "Knowledge Share with token Extended",
    "summary": "This modules allows token generation for knowledge.",
    "description": "This modules allows token generation for knowledge.",
    "author": "Megha Patel",
    "website": "",
    "category": "Productivity/Knowledge",
    "version": "16.0.1.0.0",
    "license": "LGPL-3",
    "depends": [
        "knowledge_share_with_token",
    ],
    "data": [
      "views/knowledge_article_views.xml",
    ],
    "assets": {
        'web.assets_frontend': [
            'knowledge_share_with_token_extended/static/src/js/knowledge_frontend.js',
            'knowledge_share_with_token_extended/static/src/js/knowledge_article_mixin.js'
        ],
        'web.assets_common': [
            'knowledge_share_with_token_extended/static/src/js/knowledge_article_mixin.js',
        ],
    },
}
