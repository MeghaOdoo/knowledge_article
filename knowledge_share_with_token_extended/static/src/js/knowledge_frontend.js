/** @odoo-module */
import publicWidget from 'web.public.widget';

publicWidget.registry.KnowledgeWidget.include({

    _fetchChildrenArticlesCustom: function (parentId,artToken,artParent) {
        debugger
        return this._rpc({
            route: '/knowledge/tree_panel/children',
            params: {
                parent_id: parentId,
                art_token: artToken,
                parent_art_id: artParent,
            }
        });
    },
    _renderTree: async function (active_article_id, route) {
        debugger
        const container = this.el.querySelector('.o_knowledge_tree');
        let unfoldedArticlesIds = localStorage.getItem('knowledge.unfolded.ids');
        unfoldedArticlesIds = unfoldedArticlesIds ? unfoldedArticlesIds.split(";").map(Number) : [];
        let unfoldedFavoriteArticlesIds = localStorage.getItem('knowledge.unfolded.favorite.ids');
        unfoldedFavoriteArticlesIds = unfoldedFavoriteArticlesIds ? unfoldedFavoriteArticlesIds.split(";").map(Number) : [];
        const params = new URLSearchParams(document.location.search);
        if (Boolean(params.get('auto_unfold'))) {
            unfoldedArticlesIds.push(active_article_id);
            unfoldedFavoriteArticlesIds.push(active_article_id);
        }
        debugger
        var art_token = this.el.dataset.artToken
        var parent_id = this.el.dataset.parentId
        try {
            const htmlTree = await this._rpc({
                route: route,
                params: {
                    active_article_id: active_article_id,
                    unfolded_articles_ids: unfoldedArticlesIds,
                    unfolded_favorite_articles_ids: unfoldedFavoriteArticlesIds,
                    token: art_token,
                    parent_art_id: parent_id,
                }
            });
            container.innerHTML = htmlTree;
            this._setTreeFavoriteListener();
        } catch {
            container.innerHTML = "";
        }
    },
});

