export function MicIcon({ active }: { active: boolean }) {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 22 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="relative z-10"
    >
      <rect
        x="7"
        width="8"
        height="20"
        rx="4"
        fill={active ? "#00E0FF" : "currentColor"}
      />
      <path
        d="M2 12V16C2 21.5228 6.47715 26 12 26C17.5228 26 22 21.5228 22 16V12"
        stroke={active ? "#00E0FF" : "currentColor"}
        strokeWidth="2"
      />
      <path
        d="M12 26V32"
        stroke={active ? "#00E0FF" : "currentColor"}
        strokeWidth="2"
        strokeLinecap="round"
      />
      <path
        d="M7 32H17"
        stroke={active ? "#00E0FF" : "currentColor"}
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
}

