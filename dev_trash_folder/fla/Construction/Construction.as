package {
	import flash.display.Sprite;
	import flash.display.MovieClip;
	import flash.text.TextField;
	import flash.display.DisplayObject;
	import flash.utils.getDefinitionByName;
	import flash.events.*;

	public class Construction extends Sprite {
		
		private var clipsToLoad: Array = ["labelMC_time", "labelMC_amount", "TF_titleSymbol", "TF_buildinginfo", "TF_buildinginfo2", "header_icon", "gold_icon", "time_icon", "dividers", "hammer_icon"];
		
		public function Construction() {
			super();
			var i:* = null
			var load:MovieClip = null;
			var load_textfield:TextField = null;
			for (i in this.clipsToLoad){
				trace(this.clipsToLoad[i]);
				var loadClass: Class = getDefinitionByName(this.clipsToLoad[i]) as Class;
				load = new loadClass() as MovieClip;
				load.name = this.clipsToLoad[i];
				if(load.name.indexOf("TF_") != -1){
					load_textfield = load.getChildByName("TF_Text") as TextField;
					addChild(load_textfield as TextField);
				} else {
					addChild(load as DisplayObject);
				}
				addEventListener(Event.ADDED_TO_STAGE, onAddedToStage, false, 0, true);
			}
		}
	
		private function onAddedToStage(param1: Event): void {
		}
	}
	
}
