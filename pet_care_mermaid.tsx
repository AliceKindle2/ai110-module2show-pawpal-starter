import { useEffect, useRef } from "react";

const diagram = `classDiagram
  class Owner {
    -String ownerName
    +editOwnerInfo()
  }

  class Pet {
    -String petName
    +editPetInfo()
    +addPet()
  }

  class Task {
    -String taskName
    -int duration
    -int priority
    +seeTask()
    +addTask()
    +editTask()
    +removeTask()
  }

  class Scheduler {
    -Schedule schedule
    +generateSchedule(tasks)
  }

  Owner "1" --> "1..*" Pet : has
  Owner "1" --> "0..*" Task : manages
  Task "0..*" --> "1" Scheduler : feeds
`;

export default function App() {
  const ref = useRef(null);

  useEffect(() => {
    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js";
    script.onload = () => {
      const dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      window.mermaid.initialize({
        startOnLoad: false,
        theme: dark ? "dark" : "default",
        fontFamily: "sans-serif",
        fontSize: 14,
      });
      window.mermaid.render("mermaid-svg", diagram).then(({ svg }) => {
        if (ref.current) ref.current.innerHTML = svg;
      });
    };
    document.body.appendChild(script);
    return () => document.body.removeChild(script);
  }, []);

  return (
    <div style={{ padding: "1.5rem" }}>
      <div ref={ref} style={{ display: "flex", justifyContent: "center" }} />
    </div>
  );
}
