
from odoo import fields, models, api, _


class KnowledgeArticle(models.Model):
    _inherit = 'knowledge.article'

    share_with_token =  fields.Boolean(
        string="Share with token",
    )

    @api.onchange('share_with_token')
    def _onchange_share_with_token(self):
        # Recursively update child_ids' access_token and share_with_token
        def update_share_with_token(knowledge):
            if knowledge.child_ids:
                for child in knowledge.child_ids:
                    child._origin.update({
                        'share_with_token': True
                    })
                    update_share_with_token(child)  # Recursive call

        for knowledge in self:
            if knowledge.share_with_token:
                update_share_with_token(knowledge)
            # Always set website_published to False
            knowledge.website_published = False

    @api.model
    @api.returns('knowledge.article', lambda article: article.id)
    def article_create(self, title=False, parent_id=False, is_private=False, is_article_item=False):
        res = super(KnowledgeArticle,self).article_create(title,parent_id,is_private,is_article_item)
        parent = self.browse(parent_id)
        if parent.share_with_token:
            res.share_with_token = parent.share_with_token
        return res