package com.imagelab.view.forms;

import com.imagelab.operator.miscellaneousoperators.Watershed;

import javafx.beans.value.ChangeListener;
import javafx.beans.value.ObservableValue;
import javafx.scene.control.Label;
import javafx.scene.control.Slider;
import javafx.scene.layout.VBox;

public class WatershedPropertiesForm extends AbstractPropertiesForm {
	public WatershedPropertiesForm(Watershed operator) {
		// title container
	    PropertiesFormTitleContainer WatershedTitleContainer;
	    WatershedTitleContainer = new PropertiesFormTitleContainer("Watershed");
	    
	    // Space container
	    VBox spaceContainer = new VBox();
	    spaceContainer.setPrefWidth(205.0);
	    spaceContainer.setSpacing(10);
	    Label lblSpaceOne = new Label("");
	    Label lblSpaceTwo = new Label("");
	    spaceContainer.getChildren().addAll(lblSpaceOne, lblSpaceTwo);
	    
	    // Thresold low
	    VBox lowThresholdSliderContainer = new VBox();
	    lowThresholdSliderContainer.setPrefWidth(205.0);
	    lowThresholdSliderContainer.setSpacing(10);
	    Label lblLowThresoldSlider = new Label("Low Thresold :");
	 
	    Slider lowThresoldSlider = new Slider();
	    lowThresoldSlider.setMin(0);
	    lowThresoldSlider.setMax(300);
	    lowThresoldSlider.setValue(60);
	    // enable TickLabels and Tick Marks
	    lowThresoldSlider.setShowTickLabels(true);
	    lowThresoldSlider.setShowTickMarks(true);
	    lowThresoldSlider.setBlockIncrement(50);
	    // Adding Listener to value property.
	    lowThresoldSlider.valueProperty().addListener(new ChangeListener<Number>() {

			@Override
			public void changed(ObservableValue<? extends Number> observable, Number oldValue, Number newValue) {
				// TODO Auto-generated method stub
				lblLowThresoldSlider.setText(String.format("Low Thresold : %d units", (int)newValue.doubleValue()));
				operator.setLowThreshold((int)newValue.doubleValue());
			}
	    	
		});
	    lowThresholdSliderContainer.getChildren().addAll(lblLowThresoldSlider, lowThresoldSlider);
	    
	    // Thresold high
	    VBox highThresholdSliderContainer = new VBox();
	    highThresholdSliderContainer.setPrefWidth(205.0);
	    highThresholdSliderContainer.setSpacing(10);
	    Label lblHighThresoldSlider = new Label("High Thresold :");
	 
	    Slider highThresoldSlider = new Slider();
	    highThresoldSlider.setMin(0);
	    highThresoldSlider.setMax(300);
	    highThresoldSlider.setValue(60);
	    // enable TickLabels and Tick Marks
	    highThresoldSlider.setShowTickLabels(true);
	    highThresoldSlider.setShowTickMarks(true);
	    highThresoldSlider.setBlockIncrement(50);
	    // Adding Listener to value property.
	    highThresoldSlider.valueProperty().addListener(new ChangeListener<Number>() {

			@Override
			public void changed(ObservableValue<? extends Number> observable, Number oldValue, Number newValue) {
				// TODO Auto-generated method stub
				lblHighThresoldSlider.setText(String.format("High Thresold : %d units", (int)newValue.doubleValue()));
				operator.setHighThresold((int)newValue.doubleValue());
			}
	    	
		});
	    highThresholdSliderContainer.getChildren().addAll(lblHighThresoldSlider, highThresoldSlider);
	    
	    VBox watershedContainer = new VBox();
	    watershedContainer.setPrefSize(205, 47);
	    watershedContainer.setSpacing(20);
	    watershedContainer.setLayoutX(14);
	    watershedContainer.setLayoutY(14);
	    watershedContainer.getChildren().addAll(
	    	WatershedTitleContainer,
	    	lowThresholdSliderContainer,
	    	highThresholdSliderContainer
	    );
	    getChildren().addAll(watershedContainer);
		
	}
}
