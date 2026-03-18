import { useState, useEffect, useRef } from "react";
import styles from "./LandingScreen.module.css";

const STORAGE_KEY = "imagelab:skipLanding";

const COLORS = {
  primary: "#6366f1",
  success: "#10b981",
  warning: "#f59e0b",
  background: "#0a0a0f",
  primaryLight: "#a5b4fc",
  primaryDark: "#7c3aed",
  successDark: "#059669",
} as const;

const ORBS = [
  {
    top: "10%",
    left: "15%",
    width: "400px",
    height: "400px",
    background: "radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%)",
    animation: "float1 8s ease-in-out infinite",
  },
  {
    bottom: "10%",
    right: "10%",
    width: "500px",
    height: "500px",
    background: "radial-gradient(circle, rgba(16,185,129,0.1) 0%, transparent 70%)",
    animation: "float2 10s ease-in-out infinite",
  },
  {
    top: "50%",
    right: "20%",
    width: "300px",
    height: "300px",
    background: "radial-gradient(circle, rgba(245,158,11,0.08) 0%, transparent 70%)",
    animation: "float1 12s ease-in-out infinite reverse",
  },
];

const STEPS = [
  {
    num: "01",
    title: "Load",
    desc: "Upload any image — JPEG, PNG, or GIF",
    color: COLORS.primary,
  },
  {
    num: "02",
    title: "Build",
    desc: "Drag & connect processing blocks visually",
    color: COLORS.success,
  },
  {
    num: "03",
    title: "Run",
    desc: "Execute your pipeline and see results instantly",
    color: COLORS.warning,
  },
];

interface LandingScreenProps {
  onStart: () => void;
}

export function LandingScreen({ onStart }: LandingScreenProps) {
  const [dontShowAgain, setDontShowAgain] = useState(false);
  const [visible, setVisible] = useState(false);
  const [transitioning, setTransitioning] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const raf1 = requestAnimationFrame(() => {
      const raf2 = requestAnimationFrame(() => setVisible(true));
      return () => cancelAnimationFrame(raf2);
    });
    return () => cancelAnimationFrame(raf1);
  }, []);

  useEffect(() => {
    const id = setTimeout(() => {
      buttonRef.current?.focus();
    }, 700);
    return () => clearTimeout(id);
  }, []);

  const handleStart = () => {
    if (dontShowAgain) {
      try {
        localStorage.setItem(STORAGE_KEY, "true");
      } catch {
        // storage restricted
      }
    }
    setTransitioning(true);
    onStart();
  };

  return (
    <div
      role="main"
      style={{
        height: "100vh",
        overflow: "hidden",
        background: COLORS.background,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "monospace",
        position: "relative",
      }}
    >
      <div role="status" aria-live="polite" className={styles.srOnly}>
        {transitioning ? "Loading workspace" : ""}
      </div>

      {ORBS.map((orb, i) => (
        <div
          key={i}
          aria-hidden="true"
          style={{
            position: "absolute",
            borderRadius: "50%",
            pointerEvents: "none",
            ...orb,
          }}
        />
      ))}

      <div
        aria-hidden="true"
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)
          `,
          backgroundSize: "60px 60px",
          pointerEvents: "none",
        }}
      />

      <div
        style={{
          position: "relative",
          zIndex: 10,
          maxWidth: "560px",
          width: "90%",
          padding: "1.5rem",
          opacity: visible ? 1 : 0,
          transform: visible ? "translateY(0)" : "translateY(40px)",
          transition:
            "opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1), transform 0.8s cubic-bezier(0.16, 1, 0.3, 1)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            marginBottom: "1.25rem",
            animation: visible ? "fadeUp 0.6s 0.1s ease forwards" : "none",
            opacity: 0,
          }}
        >
          <span
            style={{
              background: "rgba(99,102,241,0.15)",
              border: "1px solid rgba(99,102,241,0.3)",
              color: COLORS.primaryLight,
              padding: "5px 14px",
              borderRadius: "100px",
              fontSize: "0.72rem",
              letterSpacing: "0.15em",
              textTransform: "uppercase",
              fontFamily: "monospace",
            }}
          >
            Visual Image Processing
          </span>
        </div>

        <div
          style={{
            textAlign: "center",
            marginBottom: "0.75rem",
            animation: visible ? "fadeUp 0.6s 0.2s ease forwards" : "none",
            opacity: 0,
          }}
        >
          <h1
            style={{
              fontSize: "clamp(2.5rem, 8vw, 4rem)",
              fontWeight: 400,
              color: "#ffffff",
              margin: 0,
              lineHeight: 1.1,
              letterSpacing: "-0.02em",
              fontFamily: "monospace",
            }}
          >
            Image
            <span
              style={{
                fontStyle: "italic",
                background: `linear-gradient(135deg, ${COLORS.primary}, ${COLORS.success})`,
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              Lab
            </span>
          </h1>
          <p
            style={{
              color: "rgba(255,255,255,0.5)",
              fontSize: "0.9rem",
              marginTop: "0.5rem",
              letterSpacing: "0.05em",
              fontFamily: "monospace",
            }}
          >
            Build pipelines. Process visually. No code.
          </p>
        </div>

        <div
          aria-hidden="true"
          style={{
            height: "1px",
            background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)",
            margin: "1rem 0",
            animation: visible ? "fadeUp 0.6s 0.3s ease forwards" : "none",
            opacity: 0,
          }}
        />

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "0.5rem",
            marginBottom: "1rem",
            animation: visible ? "fadeUp 0.6s 0.4s ease forwards" : "none",
            opacity: 0,
          }}
        >
          {STEPS.map(({ num, title, desc, color }) => (
            <div
              key={num}
              className={styles.stepCard}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "1rem",
                padding: "0.65rem 1rem",
                background: "rgba(255,255,255,0.03)",
                border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: "12px",
                cursor: "default",
                transition: "background 0.2s ease, border-color 0.2s ease",
              }}
            >
              <span
                style={{
                  fontFamily: "monospace",
                  fontSize: "0.7rem",
                  color,
                  fontWeight: 700,
                  letterSpacing: "0.1em",
                  minWidth: "24px",
                }}
              >
                {num}
              </span>
              <div
                aria-hidden="true"
                style={{
                  width: "1px",
                  height: "28px",
                  background: "rgba(255,255,255,0.08)",
                }}
              />
              <div>
                <div
                  style={{
                    color: "#fff",
                    fontWeight: 600,
                    fontSize: "0.88rem",
                    marginBottom: "1px",
                  }}
                >
                  {title}
                </div>
                <div
                  style={{
                    color: "rgba(255,255,255,0.45)",
                    fontSize: "0.78rem",
                    fontFamily: "monospace",
                  }}
                >
                  {desc}
                </div>
              </div>
            </div>
          ))}
        </div>

        <div
          style={{
            animation: visible ? "fadeUp 0.6s 0.5s ease forwards" : "none",
            opacity: 0,
          }}
        >
          <button
            ref={buttonRef}
            className={styles.startBtn}
            onClick={handleStart}
            aria-label="Start Building with ImageLab"
            style={{
              width: "100%",
              padding: "0.9rem",
              background: `linear-gradient(135deg, ${COLORS.primary}, ${COLORS.success})`,
              color: "#fff",
              border: "none",
              borderRadius: "12px",
              fontSize: "0.95rem",
              fontWeight: 600,
              cursor: "pointer",
              letterSpacing: "0.05em",
              transition:
                "transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.3s ease",
              boxShadow: "0 8px 24px rgba(99,102,241,0.25)",
              fontFamily: "monospace",
            }}
          >
            Start Building
          </button>
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "center",
            marginTop: "0.6rem",
            marginBottom: "0.5rem",
            animation: visible ? "fadeUp 0.6s 0.6s ease forwards" : "none",
            opacity: 0,
          }}
        >
          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              cursor: "pointer",
              color: "rgba(255,255,255,0.5)",
              fontSize: "0.75rem",
              fontFamily: "monospace",
              letterSpacing: "0.05em",
            }}
          >
            <input
              type="checkbox"
              className={styles.checkbox}
              checked={dontShowAgain}
              onChange={(e) => setDontShowAgain(e.target.checked)}
              style={{ accentColor: COLORS.primary, cursor: "pointer" }}
            />
            {"Don't show this again"}
          </label>
        </div>
      </div>
    </div>
  );
}
