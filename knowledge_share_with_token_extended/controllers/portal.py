import werkzeug

from odoo import http, _
from odoo.http import request
from odoo.addons.knowledge.controllers.main import KnowledgeController
from odoo.osv import expression
from odoo.exceptions import AccessError


class CustomKnowledgeWebsiteController(KnowledgeController):

    @http.route(['/knowledge/article/<int:article_id>/<string:access_token>',
                 '/knowledge/article/<int:article_id>/<string:access_token>/<int:parent_art_id>/<string:parent_art_token>'], type='http',
                auth='public', website=True)
    def redirect_to_article_with_token(self, **kwargs):
        """ This route will redirect internal users to the backend view of the
        article and the share users to the frontend view instead."""
        if 'access_token' in kwargs and 'article_id' in kwargs:
            article_id = kwargs['article_id']
            access_token = kwargs['access_token']
            parent_art_token = kwargs.get('parent_art_token', False)
            parent_art_id = int(kwargs.get('parent_art_id', False))
            article = request.env['knowledge.article'].sudo().search([('id', '=', article_id)])
            if article and access_token and article.share_with_token:
                available_documents = article._get_documents_and_check_access(access_token)
                if available_documents is False:
                    return request.not_found()
                if request.env.user.has_group('base.group_user'):
                    if not article:
                        return werkzeug.exceptions.Forbidden()
                    return self._redirect_to_backend_view(article)
                if parent_art_id:
                    parent_article = request.env['knowledge.article'].sudo().search([('id', '=', parent_art_id)])
                    if parent_article._check_token(parent_art_token):
                        return self._redirect_to_portal_view_custom(article, token=parent_art_token,
                                                                    parent_art_id=parent_art_id)
                return self._redirect_to_portal_view_custom(article, token=access_token, parent_art_id=parent_art_id)
            return werkzeug.exceptions.Forbidden()

    def _redirect_to_portal_view_custom(self, article, hide_side_bar=False, token=None, parent_art_id=None):
        show_sidebar = False if hide_side_bar else self._check_sidebar_display_custom(article, token, parent_art_id)
        return request.render('knowledge.knowledge_article_view_frontend', {
            'article': article,
            'portal_readonly_mode': True,  # used to bypass access check (to speed up loading)
            'show_sidebar': show_sidebar,
            'art_token': token,
            'parent_art_id': parent_art_id,
        })

    def _check_sidebar_display_custom(self, article, token, parent_art_id=None):
        if parent_art_id:
            sr_article = request.env["knowledge.article"].sudo().search(
                [("category", "!=", "private"), ('id', '=', parent_art_id),
                 ('share_with_token', '=', True)],
                limit=1,
            )
        else:
            sr_article = request.env["knowledge.article"].sudo().search(
                [("category", "!=", "private"), ('id', '=', article.id),
                 ('share_with_token', '=', True)],
                limit=1,
            )

        if sr_article:
            return sr_article._check_token(token)
        else:
            return False

    @http.route('/knowledge/tree_panel/portal', type='json', auth='public')
    def get_tree_panel_portal(self, active_article_id=False, unfolded_articles_ids=False,
                              unfolded_favorite_articles_ids=False, token=False, parent_art_id=False):
        """ Frontend access for left panel. """
        if token:
            # request = self.with_context(art_token=token)
            request.env.context = dict(request.env.context, art_token=token, parent_art_id=parent_art_id)
        template_values = self._prepare_articles_tree_html_values(
            active_article_id,
            unfolded_articles_ids=unfolded_articles_ids,
            unfolded_favorite_articles_ids=unfolded_favorite_articles_ids
        )
        return request.env['ir.qweb']._render('knowledge.knowledge_article_tree_frontend', template_values)

    @http.route('/knowledge/tree_panel/children', type='json', auth='public', website=True, sitemap=False)
    def get_tree_panel_children(self, parent_id, art_token=None, parent_art_id=None):
        parent_verified = False
        if art_token:
            parent_sudo = request.env['knowledge.article'].sudo().search([('id', '=', parent_art_id or parent_id)])
            parent_verified = parent_sudo._check_token(art_token)
            if parent_verified:
                parent = request.env['knowledge.article'].sudo().search([('id', '=', parent_id)])
            else:
                parent = request.env['knowledge.article'].search([('id', '=', parent_id)])
        else:
            parent = request.env['knowledge.article'].search([('id', '=', parent_id)])

        if not parent:
            raise AccessError(
                _("This Article cannot be unfolded. Either you lost access to it or it has been deleted."))

        articles = parent.child_ids.filtered(
            lambda a: not a.is_article_item
        ).sorted("sequence") if parent.has_article_children else request.env['knowledge.article']

        return request.env['ir.qweb']._render('knowledge.articles_template', {
            'articles': articles,
            'parent_verified': parent_verified,
            'art_token': art_token,
            'parent_id': parent_art_id or parent_id,
            "articles_displayed_limit": self._KNOWLEDGE_TREE_ARTICLES_LIMIT,
            "articles_displayed_offset": 0,
            'portal_readonly_mode': not request.env.user.has_group('base.group_user'),
            # used to bypass access check (to speed up loading)
            "user_write_access_by_article": {
                article.id: article.user_can_write
                for article in articles
            },
            "has_parent": True
        })


def _prepare_articles_tree_html_values(self, active_article_id, unfolded_articles_ids=False,
                                       unfolded_favorite_articles_ids=False):
    """ Prepares all the info needed to render the article tree view side panel
    and returns the rendered given template with those values.

    :param int active_article_id: used to highlight the given article_id in the template;
    :param unfolded_articles_ids: List of IDs used to display the children
      of the given article ids. Unfolded articles are saved into local storage.
      When reloading/opening the article page, previously unfolded articles
      nodes must be opened;
    :param unfolded_favorite_articles_ids: same as ``unfolded_articles_ids``
      but specific for 'Favorites' tree.
    """
    art_token = request.env.context.get('art_token', False)
    parent_art_id = int(request.env.context.get('parent_art_id', False))
    unfolded_articles_ids = set(unfolded_articles_ids or [])
    unfolded_favorite_articles_ids = set(unfolded_favorite_articles_ids or [])
    existing_ids = self._article_ids_exists(unfolded_articles_ids | unfolded_favorite_articles_ids)
    unfolded_articles_ids = unfolded_articles_ids & existing_ids
    unfolded_favorite_articles_ids = unfolded_favorite_articles_ids & existing_ids

    active_article_ancestor_ids = []
    if active_article_id:
        # determine the hierarchy to unfold based on parent_path and as sudo
        # this helps avoiding to actually fetch ancestors
        # this will not leak anything as it's just a set of IDS
        # displayed articles ACLs are correctly checked here below
        active_article = request.env['knowledge.article'].sudo().browse(active_article_id)
        active_article_ancestor_ids = active_article._get_ancestor_ids()
        unfolded_articles_ids |= active_article_ancestor_ids

    active_parent_art_id = False
    if parent_art_id:
        active_parent_art_id = request.env['knowledge.article'].sudo().browse(parent_art_id)

    # fetch root article_ids as sudo, ACLs will be checked on next global call fetching 'all_visible_articles'
    # this helps avoiding 2 queries done for ACLs (and redundant with the global fetch)
    root_article_ids = request.env["knowledge.article"].sudo().search([("parent_id", "=", False)]).ids

    favorites_sudo = request.env['knowledge.article.favorite'].sudo()
    if not request.env.user._is_public():
        favorites_sudo = request.env['knowledge.article.favorite'].sudo().search([
            ("user_id", "=", request.env.user.id), ('is_article_active', '=', True)
        ])

    # Fetch all visible articles at once instead of going down the hierarchy in the template
    # using successive 'child_ids' field calls.
    # This allows to benefit from batch computation (ACLs, computes, ...).
    # We filter within the template based on the "parent_id" field to get the article children.
    all_visible_articles = request.env['knowledge.article']
    all_visible_articles_ids = unfolded_articles_ids | unfolded_favorite_articles_ids | set(root_article_ids)
    visible_favorite_article_ids = favorites_sudo.article_id.ids
    all_visible_article_domains = expression.OR([
        [
            ('id', 'child_of', all_visible_articles_ids),
            ('is_article_item', '=', False),
        ],
        [('id', 'in', visible_favorite_article_ids)],
    ])

    if all_visible_articles_ids:
        all_visible_articles = request.env['knowledge.article'].search(
            all_visible_article_domains,
            order='sequence, id',
        )
    verify_token = False
    if art_token:
        verify_token = (active_parent_art_id or active_article)._check_token(art_token)
        if verify_token:
            verified_article_domains = expression.OR([
                [
                    ('id', 'child_of', (active_parent_art_id or active_article).id),
                    ('is_article_item', '=', False),
                ],
                [('id', 'in', visible_favorite_article_ids)],
            ])
            all_visible_articles = request.env['knowledge.article'].sudo().search(
                verified_article_domains,
                order='sequence, id',
            )
    if art_token:
        root_articles = all_visible_articles.filtered(
            lambda x: x.id == (active_parent_art_id or active_article).id and x.category == 'workspace')
    else:
        root_articles = all_visible_articles.filtered(lambda article: not article.parent_id)

    user_write_access_by_article = {
        article.id: article.user_can_write
        for article in all_visible_articles
    }

    values = {
        "active_article_id": active_article_id,
        "art_token": art_token,
        "parent_verified": verify_token,
        "parent_id": (active_parent_art_id or active_article).id,
        "active_article_ancestor_ids": active_article_ancestor_ids,
        "articles_displayed_limit": self._KNOWLEDGE_TREE_ARTICLES_LIMIT,
        "articles_displayed_offset": 0,
        "all_visible_articles": all_visible_articles,
        "user_write_access_by_article": user_write_access_by_article,
        "workspace_articles": root_articles.filtered(lambda article: article.category == 'workspace'),
        "shared_articles": root_articles.filtered(lambda article: article.category == 'shared'),
        "private_articles": root_articles.filtered(
            lambda article: article.category == "private" and article.user_has_write_access),
        "unfolded_articles_ids": unfolded_articles_ids,
        "unfolded_favorite_articles_ids": unfolded_favorite_articles_ids,
        'portal_readonly_mode': not request.env.user.has_group('base.group_user'),
        "favorites_sudo": favorites_sudo,
    }

    return values


KnowledgeController._prepare_articles_tree_html_values = _prepare_articles_tree_html_values
