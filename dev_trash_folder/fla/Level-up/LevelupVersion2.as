package {
	import flash.display.Sprite;
	import flash.display.MovieClip;
	import flash.text.TextField;
	import flash.display.DisplayObject;
	import flash.utils.getDefinitionByName;
	import flash.events.*;
	import flash.external.ExternalInterface;

	public class LevelupVersion2 extends Sprite {

		private var clipsToLoad: Array = ["TF_DONATION", "TF_INFO_CURRENT_LEVEL", "SYMBOL_GOLD", "SYMBOL_SILVER", "CURRENT_LEVEL_CONTAINER", "TF_NEXTLEVEL_DONATION", "SYMBOL_NEXTLEVEL_GOLD", "SYMBOL_NEXTLEVEL_SILVER", "NEXT_LEVEL_CONTAINER", "TF_INFO_NEXT_LEVEL", "TF_INFO_NEW_QUESTS", "TF_title", "dividers", "header_icon", "stars", "BT_OK"];

		private var loadedClips: Array = [];

		public function LevelupVersion2() {
			super();
			addEventListener(Event.ADDED_TO_STAGE, onAddedToStage, false, 0, true);
			addEventListener(Event.REMOVED_FROM_STAGE, onRemovedFromStage, false, 0, true);
			
			initializeClips();
		}

		private function initializeClips(): void {
			var loadClass: Class = getDefinitionByName("LevelupVersion2Content") as Class;
			var load: MovieClip = new loadClass() as MovieClip;
			for each (var clipName:String in clipsToLoad) {
				var child: DisplayObject = load.getChildByName(clipName);
				addChild(child);
			}
		}

		private function onAddedToStage(event: Event): void {
		}

		private function onRemovedFromStage(event: Event): void {
			//cleanup();
		}

		private function cleanup(): void {
			//ExternalInterface.call("console.log", "hello!");
			// Remove all dynamically added children
			//for each(var item: DisplayObject in loadedClips) {
			//	ExternalInterface.call("console.log", "yo!");
			//	//if (item && contains(item)) {
			//	removeChild(item);
			//	//}
			//}
			//loadedClips = [];
		}
	}
}