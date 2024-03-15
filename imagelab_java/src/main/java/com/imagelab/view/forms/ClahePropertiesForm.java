package com.imagelab.view.forms;

import com.imagelab.operator.histogram.CLAHE;

import javafx.scene.layout.VBox;

public class ClahePropertiesForm extends AbstractPropertiesForm {
	public ClahePropertiesForm(CLAHE operator) {
		//Clahe title container.
        PropertiesFormTitleContainer clahePropertiesTitleContainer;
        clahePropertiesTitleContainer = new PropertiesFormTitleContainer("CLAHE");
        
        VBox clahePropertiesContainer = new VBox();
        clahePropertiesContainer.setPrefSize(205, 47);
        clahePropertiesContainer.setSpacing(20);
        clahePropertiesContainer.setLayoutX(14);
        clahePropertiesContainer.setLayoutY(14);
        clahePropertiesContainer.getChildren().addAll(
            clahePropertiesTitleContainer
        );
        getChildren().addAll(clahePropertiesContainer);
	}
}
