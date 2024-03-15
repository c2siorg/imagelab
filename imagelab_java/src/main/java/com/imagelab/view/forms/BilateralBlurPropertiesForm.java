package com.imagelab.view.forms;

import com.imagelab.operator.imagebluring.ApplyBilateralBlur;

import javafx.scene.control.Label;
import javafx.scene.control.TextField;
import javafx.scene.layout.VBox;
import javafx.scene.paint.Color;

/**
 * Applying bilateral blur effects operation related
 * UI properties form.
 */
public class BilateralBlurPropertiesForm extends AbstractPropertiesForm {
    /**
     * Builds the BilateralBlurPropertiesForm.
     *
     * @param operator - operator which requires this properties form.
     */
    public BilateralBlurPropertiesForm(ApplyBilateralBlur operator) {
        //Bilateral blur tittle container.
        PropertiesFormTitleContainer bilateralBlurTitleContainer;
        bilateralBlurTitleContainer = new PropertiesFormTitleContainer("Bilateral Blur Properties");

        //Diameter
        VBox diameterContainer = new VBox();
        diameterContainer.setPrefWidth(205.0);
        diameterContainer.setSpacing(10);
        Label lblDiameter = new Label("Diameter");
        TextField diameterTextField = new TextField(String.valueOf(15.0));
        diameterTextField.setPrefSize(205.0, 27.0);
        Label lblErrDiameter = new Label("Error");
        lblErrDiameter.setTextFill(Color.web("#f20028"));
        lblErrDiameter.setVisible(false);
        //Listener to capture text change.
        diameterTextField.textProperty().addListener((observable, oldValue, newValue) -> {
            int newVal;
            if ("".equals(newValue)) {
                newVal = 0;
                lblErrDiameter.setVisible(true);
                lblErrDiameter.setText("Enter a value");
            } else {
                try{
                    newVal = Integer.parseInt(newValue);
                    lblErrDiameter.setVisible(false);
                    operator.setDiameter(newVal);
                } catch(Exception e) {
                    lblErrDiameter.setVisible(true);
                    lblErrDiameter.setText("Enter an Integer");
                }
            }
        });
        diameterContainer.getChildren().addAll(lblDiameter, diameterTextField, lblErrDiameter);

        //Sigma Space
        VBox sigmaSpaceContainer = new VBox();
        sigmaSpaceContainer.setPrefWidth(205.0);
        sigmaSpaceContainer.setSpacing(10);
        Label lblSigmaSpace = new Label("Sigma Space");
        TextField sigmaSpaceTextField = new TextField(String.valueOf(80));
        sigmaSpaceTextField.setPrefSize(205.0, 27.0);
        Label lblSigmaSpaceErr = new Label("Error");
        lblSigmaSpaceErr.setTextFill(Color.web("#f20028"));
        lblSigmaSpaceErr.setVisible(false);
        //Listener to capture text change.
        sigmaSpaceTextField.textProperty().addListener((observable, oldValue, newValue) -> {
            int newVal;
            if ("".equals(newValue)) {
                newVal = 0;
                lblSigmaSpaceErr.setVisible(true);
                lblSigmaSpaceErr.setText("Enter a value");
            } else {
                try{
                    newVal = Integer.parseInt(newValue);
                    lblSigmaSpaceErr.setVisible(false);
                    operator.setsigmaSpace(newVal);
                } catch(Exception e) {
                    lblSigmaSpaceErr.setVisible(true);
                    lblSigmaSpaceErr.setText("Enter an Integer");
                }
            }
        });
        sigmaSpaceContainer.getChildren().addAll(lblSigmaSpace, sigmaSpaceTextField, lblSigmaSpaceErr);

        //Sigma Colour
        VBox sigmaColorContainer = new VBox();
        sigmaColorContainer.setPrefWidth(205.0);
        sigmaColorContainer.setSpacing(10);
        Label lblSigmaColor = new Label("Sigma Colour");
        TextField sigmaColorTextField = new TextField(String.valueOf(80));
        sigmaColorTextField.setPrefSize(205.0, 27.0);
        Label lblSigmaColorErr = new Label("Error");
        lblSigmaColorErr.setTextFill(Color.web("#f20028"));
        lblSigmaColorErr.setVisible(false);
        //Listener to capture text change.
        sigmaColorTextField.textProperty().addListener((observable, oldValue, newValue) -> {
            int newVal;
            if ("".equals(newValue)) {
                newVal = 0;
                lblSigmaColorErr.setVisible(true);
                lblSigmaColorErr.setText("Enter a value");
            } else {
                try{
                    newVal = Integer.parseInt(newValue);
                    lblSigmaColorErr.setVisible(false);
                    operator.setsigmaColor(newVal);
                } catch(Exception e) {
                    lblSigmaColorErr.setVisible(true);
                    lblSigmaColorErr.setText("Enter an Integer");
                }
            }
        });
        sigmaColorContainer.getChildren().addAll(lblSigmaColor, sigmaColorTextField, lblSigmaColorErr);

        VBox bilateralBlurPropertiesContainer = new VBox();
        bilateralBlurPropertiesContainer.setPrefSize(205, 47);
        bilateralBlurPropertiesContainer.setSpacing(20);
        bilateralBlurPropertiesContainer.setLayoutX(14);
        bilateralBlurPropertiesContainer.setLayoutY(14);
        bilateralBlurPropertiesContainer.getChildren().addAll(
                bilateralBlurTitleContainer,
                diameterContainer,
                sigmaSpaceContainer,
                sigmaColorContainer
        );
        getChildren().addAll(bilateralBlurPropertiesContainer);
    }
}
