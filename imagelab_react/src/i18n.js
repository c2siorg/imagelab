import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";
const resources = {
  en: {
    translation: {
      paragraph: "internationalization",
    },
  },
  si: {
    translation: {
      paragraph: "ජාත්යන්තරකරණය",
    },
  },
  ta: {
    translation: {
      paragraph: "சர்வதேசமயமாக்கல்",
    },
  },
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    lng: "en",
    fallbackLng: "si",
    interpolation: {
      escapeValue: false, // not needed for react as it escapes by default
    },
  });

export default i18n;
