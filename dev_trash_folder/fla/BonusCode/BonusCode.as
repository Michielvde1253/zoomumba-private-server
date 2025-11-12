package {
	import flash.display.Sprite;
	import flash.display.MovieClip;
	import flash.text.TextField;
	import flash.display.DisplayObject;
	import flash.utils.getDefinitionByName;
	import flash.events.*;
	import flash.external.ExternalInterface;

	public class BonusCode extends Sprite {

		private var clipsToLoad: Array = ["txt_title", "SC_TF_ASK", "textbox", "header_icon", "dividers", "bonusText", "BT_CANCEL", "BT_OK"];

		private var loadedClips: Array = [];

		public function BonusCode() {
			super();
			addEventListener(Event.ADDED_TO_STAGE, onAddedToStage, false, 0, true);
			addEventListener(Event.REMOVED_FROM_STAGE, onRemovedFromStage, false, 0, true);
			
			initializeClips();
		}

		private function initializeClips(): void {
			var loadClass: Class = getDefinitionByName("BonusCodeContent") as Class;
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