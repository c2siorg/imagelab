package com.imagelab.controllers;

import com.imagelab.component.OperatorUIElement;
import com.imagelab.operator.histogram.CLAHE;
import com.imagelab.operator.histogram.HistogramCalculation;
import com.imagelab.operator.histogram.TemplateMatching;
import com.imagelab.view.AbstractInformationUI;
import com.imagelab.view.InformationContainerView;
import com.imagelab.view.forms.AbstractPropertiesForm;
import com.imagelab.view.forms.ClahePropertiesForm;
import com.imagelab.view.forms.HistogramCalculationPropertiesForm;
import com.imagelab.view.forms.TemplateMatchingPropertiesForm;

public class HistogramController {
	public static OperatorUIElement histogramCalculationElement() {
		//Histogram Calculation UI element.
        OperatorUIElement histogramCalculation = new OperatorUIElement() {
            @Override
            public AbstractInformationUI buildInformationUI() {
                return new InformationContainerView(HistogramCalculation
                        .Information.OPERATOR_INFO.toString());
            }

            @Override
            public AbstractPropertiesForm buildPropertiesFormUI() {
                return new HistogramCalculationPropertiesForm((HistogramCalculation) this.operator);
            }
        };
        histogramCalculation.operator = new HistogramCalculation();
        histogramCalculation.operatorId = HistogramCalculation.class.getCanonicalName();
        histogramCalculation.operatorName = "HISTOGRAM";
        histogramCalculation.elementStyleId = "calHist";
        histogramCalculation.buildElement();
        return histogramCalculation;
	}
	public static OperatorUIElement templateMatchingElement() {
		//Template Matching Controller Function
        OperatorUIElement templateMatching = new OperatorUIElement() {
            @Override
            public AbstractInformationUI buildInformationUI() {
                return new InformationContainerView(TemplateMatching
                        .Information.OPERATOR_INFO.toString());
            }

            @Override
            public AbstractPropertiesForm buildPropertiesFormUI() {
                return new TemplateMatchingPropertiesForm((TemplateMatching) this.operator);
            }
        };
        templateMatching.operator = new TemplateMatching();
        templateMatching.operatorId = TemplateMatching.class.getCanonicalName();
        templateMatching.operatorName = "TEMPLATE-MATCH";
        templateMatching.elementStyleId = "templateMatch";
        templateMatching.buildElement();
        return templateMatching;
	}
    public static OperatorUIElement claheElement() {
		//CLAHE Controller Function
        OperatorUIElement claheElement = new OperatorUIElement() {
            @Override
            public AbstractInformationUI buildInformationUI() {
                return new InformationContainerView(CLAHE
                        .Information.OPERATOR_INFO.toString());
            }

            @Override
            public AbstractPropertiesForm buildPropertiesFormUI() {
                return new ClahePropertiesForm((CLAHE) this.operator);
            }
        };
        claheElement.operator = new CLAHE();
        claheElement.operatorId = CLAHE.class.getCanonicalName();
        claheElement.operatorName = "CLAHE";
        claheElement.elementStyleId = "clahe";
        claheElement.buildElement();
        return claheElement;
	}
}
