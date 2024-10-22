/** @odoo-module */
import KnowledgeTreePanelMixin from '@knowledge/js/tools/tree_panel_mixin';

KnowledgeTreePanelMixin._fold = async function ($button, isFavoriteTree) {
   debugger;
   const $icon = $button.find('i');
   const $li = $button.closest('li');
   const articleId = $li.data('articleId').toString();
   if ($icon.hasClass('fa-caret-down')) {
       // Hiding ul breaks nestedSortable, so move children
       // inside sibling to not lose its content
       const $ul = $li.find('> ul');
       $li.find('> div').append($ul.detach().hide());
       this._removeUnfolded(articleId, isFavoriteTree);
       $icon.removeClass('fa-caret-down');
       $icon.addClass('fa-caret-right');
   } else {
       const $ul = $li.find('> div > ul');
       if ($ul.length) {
           // Show children content stored in sibling
           $li.append($ul.detach().show());
       } else {
           let children;
           try {
                if ($li.data('artToken')){
                    children = await this._fetchChildrenArticlesCustom($li.data('articleId'),$li.data('artToken'),$li.data('parentId'));
                }
                else{
                    children = await this._fetchChildrenArticles($li.data('articleId'));
                }
           } catch (error) {
               // Article is not accessible anymore, remove it from the sidebar
               $li.remove();
               throw error;
           }
           const $newUl = $('<ul/>').append(children);
           $li.append($newUl);
       }
       this._addUnfolded(articleId, isFavoriteTree);
       $icon.removeClass('fa-caret-right');
       $icon.addClass('fa-caret-down');
   }
}

return KnowledgeTreePanelMixin