var CTRL = null;

angular
	.module('myapp', ['ngMaterial', 'ngAnimate', 'lfNgMdFileInput'])
	.controller('MainController', function($scope, $sce, $http, $timeout){
		var ctrl = this;
		
		// For debugging
		CTRL = ctrl;
		ctrl.tabs = []
		ctrl.isLoading = false;

		ctrl.selectedIndex = 0
		ctrl.parachoice = false
		ctrl.parachoice_label = 'Rise, Rotation'
		ctrl.expertchoice = false
		ctrl.expertchoice_label = 'No Expert'
		ctrl.sliderListShow = []

		ctrl.parachoice_onClick = function(){
			if (ctrl.parachoice == false){
				ctrl.parachoice_label = 'Rise, Rotation'
			}
			else{
				ctrl.parachoice_label = 'Pitch, # of Units'
			}
			ctrl.update_sliderListShow();
		}

		ctrl.expertchoice_onClick = function(){
			if (ctrl.expertchoice == false){
				ctrl.expertchoice_label = 'No Expert'
			}
			else{
				ctrl.expertchoice_label = 'Expert'
			}
			ctrl.update_sliderListShow();
		}

		ctrl.update_sliderListShow = function(){
			ctrl.sliderListShow = ctrl.sliderList.filter(function(a){
			    return a.group != ctrl.parachoice|0;
				})
			if (ctrl.expertchoice == false){
				ctrl.sliderListShow = ctrl.sliderListShow.filter(function(a){
			    return a.group != 3;
				})
			}
		}


		ctrl.uploadData = function(){
			var f = ctrl.files[0];
	    	ctrl.fd = new FormData();
	    	
			if (typeof f != 'undefined'){
				ctrl.fd.append('file', f.lfFile);
			}
			
			ctrl.fd.append('rise', ctrl.sliderList[2].model);
			ctrl.fd.append('rotation', ctrl.sliderList[3].model);
			ctrl.fd.append('helixwidth', ctrl.sliderList[4].model);
			ctrl.fd.append('pixelsize', ctrl.sliderList[5].model);
			ctrl.fd.append('highres', ctrl.sliderList[6].model);
			ctrl.fd.append('lowres', ctrl.sliderList[7].model);
			ctrl.fd.append('sym', ctrl.sliderList[8].model);
			ctrl.fd.append('powersize', ctrl.sliderList[9].model);
			ctrl.fd.append('bfactor', ctrl.sliderList[10].model);
			ctrl.isLoading = true;

			$http(
				{
				
				method: "POST",
				url: "/upload",
				data: ctrl.fd,
				headers: { 'Content-Type': undefined},
				// 'Content-Type': undefined 'multipart/form-data'
				transformRequest: angular.identity
				}
				).then(function(mes){
//					console.log(mes.data);
					ctrl.tabs.push({
						"label": mes.data.label,
						"html1": $sce.trustAsHtml(mes.data.div1),
						"html2": $sce.trustAsHtml(mes.data.div2),
						"params": $sce.trustAsHtml(mes.data.parameters),
						"layerlines": $sce.trustAsHtml(mes.data.layerlines),
						"secondLocked": mes.data.justsim
						});

					$timeout(function(){
					script1 = mes.data.script1.split(/\n/).slice(2,-1).join("\n");
					script2 = mes.data.script2.split(/\n/).slice(2,-1).join("\n");
					eval(script1);
					eval(script2);
					}, 1000)
					ctrl.isLoading = false;
				})
		  	
			}


		ctrl.sliderList = [
			{"model":23.04, "min":0, "max":500,"step":0.001, 
			"label":"Pitch \u212B", "group":0}, 

			{"model":16.34, "min":1, "max":100,"step":0.001, 
			"label":"# Units per Turn", "group":0}, 

			{"model":1.408, "min":0, "max":100,"step":0.001, 
			"label":"Subunit Rise \u212B", "group":1}, 

			{"model":22.04, "min":1, "max":180,"step":0.001, 
			"label":"Subunit Rotation in \u00B0", "group":1}, 

			{"model":90, "min":5, "max":500,"step":1, 
			"label":"Mean Helix Width \u212B", "group":2}, 

			{"model":1.35, "min":1, "max":50,"step":0.001, 
			"label":"Pixel Size Upload \u212B","group":2}, 

			{"model":5, "min":2, "max":40,"step":1,
			"label":"High Res cutoff \u212B","group":3}, 

			{"model":300, "min":100, "max":1000,"step":50,
			"label":"Low Res cutoff \u212B","group":3},

			{"model":1, "min":1, "max":16,"step":1,
			"label":"Rotational Symmetry of Helix","group":3},

			{"model":500, "min":50, "max":1000,"step":50,
			"label":"Level of Detail Pixel","group":3}, 

			{"model":100, "min":4, "max":10000,"step":10,
			"label":"Sim. B-Factor \u212B\u00B2","group":3}
			]

		ctrl.removeTab = function(tab) {
      		var index = ctrl.tabs.indexOf(tab);
      		ctrl.tabs.splice(index, 1);
      		ctrl.selectedIndex = ctrl.selectedIndex-1
      	}


		ctrl.updateHelixParams = function(slider) {
			if (slider.group == 0){
				return updateRiseRot();
			}
			else if (slider.group == 1){
				return updatePitchUnits();
			}
		}

		ctrl.setHelixParams = function(rise, rot, wid){
			ctrl.sliderList[2].model = rise;
			ctrl.sliderList[3].model = rot;
			ctrl.sliderList[4].model = wid;
			return updatePitchUnits();
		}

		function updateRiseRot() {
			pitch = ctrl.sliderList[0].model
			unitturn = ctrl.sliderList[1].model
			// ctrl.sliderList[0].model = Math.round(pitch*100.0)/100.0
			// ctrl.sliderList[1].model = Math.round(unitturn*100.0)/100.0
		    ctrl.sliderList[2].model = Math.round(pitch/unitturn*1000.0)/1000.0
		    ctrl.sliderList[3].model = Math.round(360.0 / unitturn*1000.0)/1000.0
		};

		function updatePitchUnits() {
			rise = ctrl.sliderList[2].model
			rotation = ctrl.sliderList[3].model
			ctrl.sliderList[1].model = Math.round(360.0 / rotation*1000)/1000
			unitturn = ctrl.sliderList[1].model
		    ctrl.sliderList[0].model = Math.round(rise*unitturn*1000)/1000
		    // ctrl.sliderList[2].model = Math.round(rise*100)/100
		    // ctrl.sliderList[3].model = Math.round(rotation*100)/100
		};

		ctrl.update_sliderListShow()


	})

	.config(function($mdThemingProvider) {
	  $mdThemingProvider.theme('default')
	    .primaryPalette('green')
	    .warnPalette('red')
	    .accentPalette('grey');
	});


