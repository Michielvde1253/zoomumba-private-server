package {
	import flash.display.Sprite;
	import flash.display.MovieClip;
	import flash.text.TextField;
	import flash.display.DisplayObject;
	import flash.utils.getDefinitionByName;
	import flash.events.*;

	public class Animalbreed extends Sprite {
		
		private var clipsToLoad: Array = ["labelMC_time", "labelMC_breedInfo", "labelMC_instantBaby", "labelMC_amount", "labelMC_cost", "TF_titleSymbol", "header_icon", "breed_icon", "dummy_icon", "silver_icon", "gold_icon", "time_icon", "dividers", "TF_descriptionSymbol", "TF_instantdescriptionSymbol"];
		
		public function Animalbreed() {
			super();
			var i:* = null
			var load:MovieClip = null;
			var load_textfield:TextField = null;
			for (i in this.clipsToLoad){
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
