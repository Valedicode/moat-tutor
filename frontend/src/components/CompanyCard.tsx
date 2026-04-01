"use client";

import { Company } from "@/types/company";

type CompanyCardProps = {
  company: Company;
  isSelected: boolean;
  onToggle: () => void;
};

export function CompanyCard({ company, isSelected, onToggle }: CompanyCardProps) {
  return (
    <button
      onClick={onToggle}
      className="flex flex-col items-center gap-3 rounded-[28px] border-2 p-6 transition-all duration-300 hover:scale-[1.02]"
      style={{
        borderColor: isSelected ? "var(--accent)" : "transparent",
        backgroundColor: isSelected
          ? "color-mix(in srgb, var(--accent) 5%, transparent)"
          : "color-mix(in srgb, var(--surface) 75%, transparent)",
        boxShadow: isSelected 
          ? "none" 
          : "0 0 0 1px var(--border)",
      }}
    >
      {/* Company Logo/Icon */}
      <div
        className="flex h-16 w-16 items-center justify-center rounded-2xl"
        style={{
          backgroundColor: isSelected
            ? "color-mix(in srgb, var(--accent) 15%, transparent)"
            : "var(--surface-secondary)",
        }}
      >
        {company.id === "aapl" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "var(--text-primary)" }}>
            <path d="M17.05 20.28c-.98.95-2.05.8-3.08.35-1.09-.46-2.09-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/>
          </svg>
        )}
        {company.id === "nvda" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#76b900" }}>
            <path d="M3.5 3v18h17V3h-17zm3.5 4.5h10v1.5H7v-1.5zm0 3h10v1.5H7v-1.5zm0 3h10V15H7v-1.5z"/>
          </svg>
        )}
        {company.id === "msft" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="none">
            <rect x="3" y="3" width="8" height="8" fill={isSelected ? "var(--accent)" : "#F25022"} />
            <rect x="13" y="3" width="8" height="8" fill={isSelected ? "var(--accent)" : "#7FBA00"} />
            <rect x="3" y="13" width="8" height="8" fill={isSelected ? "var(--accent)" : "#00A4EF"} />
            <rect x="13" y="13" width="8" height="8" fill={isSelected ? "var(--accent)" : "#FFB900"} />
          </svg>
        )}
        {company.id === "googl" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "var(--text-primary)" }}>
            <path d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"/>
          </svg>
        )}
        {company.id === "avgo" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#e53935" }}>
            <path d="M12 2L3 7v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5zm0 10h7c-.53 4.12-3.28 7.79-7 8.94V12H5V7.89l7-3.78v7.89z"/>
          </svg>
        )}
        {company.id === "orcl" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#f80000" }}>
            <path d="M17.5 4h-11C4.5 4 3 5.5 3 7.5v9C3 18.5 4.5 20 6.5 20h11c2 0 3.5-1.5 3.5-3.5v-9C21 5.5 19.5 4 17.5 4zm1 12.5c0 .83-.67 1.5-1.5 1.5h-11c-.83 0-1.5-.67-1.5-1.5v-9c0-.83.67-1.5 1.5-1.5h11c.83 0 1.5.67 1.5 1.5v9z"/>
            <path d="M7 12c0-2.76 2.24-5 5-5s5 2.24 5 5-2.24 5-5 5-5-2.24-5-5zm2 0c0 1.66 1.34 3 3 3s3-1.34 3-3-1.34-3-3-3-3 1.34-3 3z"/>
          </svg>
        )}
        {company.id === "amd" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#ed1c24" }}>
            <path d="M3 3l6 18h3L18 3h-3l-4.5 13.5L6 3H3zm15 0l3 9v9h-6l-3-9h3l1.5 4.5L18 9h-3l3-6z"/>
          </svg>
        )}
        {company.id === "csco" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#049fd9" }}>
            <path d="M3 14h2v7H3v-7zm4-4h2v11H7V10zm4-7h2v18h-2V3zm4 4h2v14h-2V7zm4 3h2v11h-2V10z"/>
          </svg>
        )}
        {company.id === "pltr" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "var(--text-primary)" }}>
            <path d="M12 2L2 7v10l10 5 10-5V7L12 2zm0 2.18l7.6 3.8L12 11.78l-7.6-3.8L12 4.18zM4 9.19l7 3.5v7.12l-7-3.5V9.19zm16 0v7.12l-7 3.5v-7.12l7-3.5z"/>
          </svg>
        )}
        {company.id === "mu" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#0079c1" }}>
            <path d="M3 3v18h18V3H3zm16 16H5V5h14v14z"/>
            <path d="M7 7v10h2V9.5L11 14l2-4.5V17h2V7h-2l-2 5-2-5H7z"/>
          </svg>
        )}
        {company.id === "adbe" && (
          <svg className="h-10 w-10" viewBox="0 0 256 228" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#FF0000" }}>
            <path d="M94.684 0L0 226.54V0z"/>
            <path d="M256 0v226.54L161.353 0z"/>
            <path d="M128.024 83.527l60.288 143.042h-39.513l-18.038-45.554H86.642z"/>
          </svg>
        )}
        {company.id === "crm" && (
          <svg className="h-10 w-10" viewBox="0 0 256 180" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#00A1E0" }}>
            <path d="M106.553 19.651c8.248-8.594 19.731-13.924 32.43-13.924c16.883 0 31.612 9.414 39.455 23.389a54.5 54.5 0 0 1 22.3-4.74c30.449 0 55.134 24.9 55.134 55.615c0 30.719-24.685 55.62-55.134 55.62a54.7 54.7 0 0 1-10.86-1.083c-6.908 12.321-20.07 20.645-35.178 20.645a40.1 40.1 0 0 1-17.632-4.058c-7.002 16.47-23.316 28.019-42.33 28.019c-19.8 0-36.674-12.529-43.152-30.1c-2.83.602-5.763.915-8.772.915c-23.574 0-42.686-19.308-42.686-43.13a43.2 43.2 0 0 1 21.345-37.36a49.4 49.4 0 0 1-4.088-19.727C17.385 22.336 39.626.128 67.06.128c16.106 0 30.42 7.658 39.494 19.523z"/>
          </svg>
        )}
        {company.id === "now" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#81B5A1" }}>
            <path d="M5 20V4h3l8 11V4h3v16h-3L8 9v11z"/>
          </svg>
        )}
        {company.id === "wday" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#005CB9" }}>
            <path d="M4 15a8 8 0 0 1 16 0z" opacity="0.9"/>
            <path d="M2 17h20v2H2z"/>
            <rect x="11" y="3" width="2" height="3.5" rx="1"/>
            <rect x="17" y="5.5" width="2" height="3.5" rx="1" transform="rotate(45 18 7.25)"/>
            <rect x="5" y="5.5" width="2" height="3.5" rx="1" transform="rotate(-45 6 7.25)"/>
          </svg>
        )}
        {company.id === "veev" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#F68D2E" }}>
            <path d="M2 4h4.5l5.5 14.5L17.5 4H22L12 22z"/>
          </svg>
        )}
        {company.id === "ddog" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#632CA6" }}>
            <path d="M19.57 17.04l-1.997-1.316-1.665 2.782-1.937-.567-1.706 2.604.087.82 9.274-1.71-.538-5.794zm-8.649-2.498l1.488-.204c.241.108.409.15.697.223.45.117.97.23 1.741-.16.18-.088.553-.43.704-.625l6.096-1.106.622 7.527-10.444 1.882zm11.325-2.712l-.602.115L20.488 0L.789 2.285l2.427 19.693l2.306-.334c-.184-.263-.471-.581-.96-.989-.68-.564-.44-1.522-.039-2.127.53-1.022 3.26-2.322 3.106-3.956-.056-.594-.15-1.368-.702-1.898-.02.22.017.432.017.432s-.227-.289-.34-.683c-.112-.15-.2-.199-.319-.4-.085.233-.073.503-.073.503s-.186-.437-.216-.807c-.11.166-.137.48-.137.48s-.241-.69-.186-1.062c-.11-.323-.436-.965-.343-2.424.6.421 1.924.321 2.44-.439.171-.251.288-.939-.086-2.293-.24-.868-.835-2.16-1.066-2.651l-.028.02c.122.395.374 1.223.47 1.625.293 1.218.372 1.642.234 2.204-.116.488-.397.808-1.107 1.165-.71.358-1.653-.514-1.713-.562-.69-.55-1.224-1.447-1.284-1.883-.062-.477.275-.763.445-1.153-.243.07-.514.192-.514.192s.323-.334.722-.624c.165-.109.262-.178.436-.323a9.762 9.762 0 0 0-.456.003s.42-.227.855-.392c-.318-.014-.623-.003-.623-.003s.937-.419 1.678-.727c.509-.208 1.006-.147 1.286.257.367.53.752.817 1.569.996.501-.223.653-.337 1.284-.509.554-.61.99-.688.99-.688s-.216.198-.274.51c.314-.249.66-.455.66-.455s-.134.164-.259.426l.03.043c.366-.22.797-.394.797-.394s-.123.156-.268.358c.277-.002.838.012 1.056.037 1.285.028 1.552-1.374 2.045-1.55.618-.22.894-.353 1.947.68.903.888 1.609 2.477 1.259 2.833-.294.295-.874-.115-1.516-.916a3.466 3.466 0 0 1-.716-1.562 1.533 1.533 0 0 0-.497-.85s.23.51.23.96c0 .246.03 1.165.424 1.68-.039.076-.057.374-.1.43-.458-.554-1.443-.95-1.604-1.067.544.445 1.793 1.468 2.273 2.449.453.927.186 1.777.416 1.997.065.063.976 1.197 1.15 1.767.306.994.019 2.038-.381 2.685l-1.117.174c-.163-.045-.273-.068-.42-.153.08-.143.241-.5.243-.572l-.063-.111c-.348.492-.93.97-1.414 1.245-.633.359-1.363.304-1.838.156-1.348-.415-2.623-1.327-2.93-1.566 0 0-.01.191.048.234.34.383 1.119 1.077 1.872 1.56l-1.605.177.759 5.908c-.337.048-.39.071-.757.124-.325-1.147-.946-1.895-1.624-2.332-.599-.384-1.424-.47-2.214-.314l-.05.059a2.851 2.851 0 0 1 1.863.444c.654.413 1.181 1.481 1.375 2.124.248.822.42 1.7-.248 2.632-.476.662-1.864 1.028-2.986.237.3.481.705.876 1.25.95.809.11 1.577-.03 2.106-.574.452-.464.69-1.434.628-2.456l.714-.104.258 1.834 11.827-1.424zM15.05 6.848c-.034.075-.085.125-.007.37l.004.014.013.032.032.073c.14.287.295.558.552.696.067-.011.136-.019.207-.023.242-.01.395.028.492.08.009-.048.01-.119.005-.222-.018-.364.072-.982-.626-1.308-.264-.122-.634-.084-.757.068a.302.302 0 0 1 .058.013c.186.066.06.13.027.207m1.958 3.392c-.092-.05-.52-.03-.821.005-.574.068-1.193.267-1.328.372-.247.191-.135.523.047.66.511.382.96.638 1.432.575.29-.038.546-.497.728-.914.124-.288.124-.598-.058-.698m-5.077-2.942c.162-.154-.805-.355-1.556.156-.554.378-.571 1.187-.041 1.646.053.046.096.078.137.104a4.77 4.77 0 0 1 1.396-.412c.113-.125.243-.345.21-.745-.044-.542-.455-.456-.146-.749"/>
          </svg>
        )}
        {company.id === "tyl" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#004976" }}>
            <path d="M3 4h18v4.5h-7V20h-4V8.5H3z"/>
          </svg>
        )}
        {company.id === "fico" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#003A70" }}>
            <path d="M5 4h14v4H10v3h8v4h-8v5H5z"/>
          </svg>
        )}
        {company.id === "nxpi" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#00479D" }}>
            <path d="m6.797 7.914 2.52 4.086-2.52 4.086-4.271-4.938.001 4.938L0 16.08V7.914h2.524l4.271 4.939.001-4.939m14.85 2.895c0-.552-.273-.868-1.036-.868h-3.188v2.312h3.404c.593 0 .82-.558.82-1.042v-.402zm-.63-2.895C23.42 7.914 24 9.108 24 10.707v.96c0 1.217-.535 2.614-2.323 2.614h-4.259l.001 1.805h-.001L14.897 12l2.521-4.086h3.598m-6.745 0h-.462l-1.701 2.717-1.702-2.716H7.418l2.521 4.086-2.521 4.086h2.987l1.702-2.716 1.702 2.716h.466l2.52-.001-2.52-4.085 2.52-4.086h-2.525z"/>
          </svg>
        )}
        {company.id === "amat" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#005CAB" }}>
            <path d="M12 2L3 22h4.5l1.5-4h6l1.5 4H21L12 2zm0 7l2.5 7h-5L12 9z"/>
          </svg>
        )}
        {company.id === "entg" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#1D428A" }}>
            <path d="M5 4h14v3.5H10v3h8v3.5h-8v3h9V21H5z"/>
          </svg>
        )}
        {company.id === "ftnt" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#EE3124" }}>
            <path d="M0 9.785h6.788v4.454H0zm8.666-6.33h6.668v4.453H8.666zm0 12.637h6.668v4.454H8.666zm8.522-6.307H24v4.454h-6.812zM2.792 3.455C1.372 3.814.265 5.404 0 7.425v.506h6.788V3.454zM0 16.091v.554c.24 1.926 1.276 3.466 2.624 3.9h4.188v-4.454zm24-8.184v-.506c-.265-1.998-1.372-3.587-2.792-3.972h-4.02v4.454H24zM21.376 20.57c1.324-.458 2.36-1.974 2.624-3.9v-.554h-6.812v4.454z"/>
          </svg>
        )}
        {company.id === "panw" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#F04E23" }}>
            <path d="m10.278 15.443 1.705 1.705-3.426 3.426-3.427-3.426 8.592-8.591-1.705-1.705 3.426-3.426 3.427 3.426-8.592 8.591zM0 12.017l3.426 3.426 8.591-8.59-3.426-3.427L0 12.017zm11.983 5.13 3.426 3.427L24 11.983l-3.426-3.426-8.591 8.59z"/>
          </svg>
        )}
        {company.id === "meta" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#0467DF" }}>
            <path d="M6.915 4.03c-1.968 0-3.683 1.28-4.871 3.113C.704 9.208 0 11.883 0 14.449c0 .706.07 1.369.21 1.973a6.624 6.624 0 0 0 .265.86 5.297 5.297 0 0 0 .371.761c.696 1.159 1.818 1.927 3.593 1.927 1.497 0 2.633-.671 3.965-2.444.76-1.012 1.144-1.626 2.663-4.32l.756-1.339.186-.325c.061.1.121.196.183.3l2.152 3.595c.724 1.21 1.665 2.556 2.47 3.314 1.046.987 1.992 1.22 3.06 1.22 1.075 0 1.876-.355 2.455-.843a3.743 3.743 0 0 0 .81-.973c.542-.939.861-2.127.861-3.745 0-2.72-.681-5.357-2.084-7.45-1.282-1.912-2.957-2.93-4.716-2.93-1.047 0-2.088.467-3.053 1.308-.652.57-1.257 1.29-1.82 2.05-.69-.875-1.335-1.547-1.958-2.056-1.182-.966-2.315-1.303-3.454-1.303zm10.16 2.053c1.147 0 2.188.758 2.992 1.999 1.132 1.748 1.647 4.195 1.647 6.4 0 1.548-.368 2.9-1.839 2.9-.58 0-1.027-.23-1.664-1.004-.496-.601-1.343-1.878-2.832-4.358l-.617-1.028a44.908 44.908 0 0 0-1.255-1.98c.07-.109.141-.224.211-.327 1.12-1.667 2.118-2.602 3.358-2.602zm-10.201.553c1.265 0 2.058.791 2.675 1.446.307.327.737.871 1.234 1.579l-1.02 1.566c-.757 1.163-1.882 3.017-2.837 4.338-1.191 1.649-1.81 1.817-2.486 1.817-.524 0-1.038-.237-1.383-.794-.263-.426-.464-1.13-.464-2.046 0-2.221.63-4.535 1.66-6.088.454-.687.964-1.226 1.533-1.533a2.264 2.264 0 0 1 1.088-.285z"/>
          </svg>
        )}
        {company.id === "msi" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#005A8B" }}>
            <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12C24.002 5.375 18.632.002 12.007 0H12zm7.327 18.065s-.581-2.627-1.528-4.197c-.514-.857-1.308-1.553-2.368-1.532-.745 0-1.399.423-2.2 1.553-.469.77-.882 1.573-1.235 2.403 0 0-.29-.675-.63-1.343a8.038 8.038 0 0 0-.605-1.049c-.804-1.13-1.455-1.539-2.2-1.553-1.049-.021-1.854.675-2.364 1.528-.948 1.574-1.528 4.197-1.528 4.197h-.864l4.606-15.12 3.56 11.804.024.021.024-.021 3.56-11.804 4.61 15.113h-.862z"/>
          </svg>
        )}
        {company.id === "br" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#000C36" }}>
            <path d="M3 6h7l3 3-3 3H3zm0 6h7l3 3-3 3H3z"/>
            <path d="M21 6h-7l-3 3 3 3h7zm0 6h-7l-3 3 3 3h7z"/>
          </svg>
        )}
        {company.id === "tru" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#00A6CA" }}>
            <path d="M3 4h18v4.5h-7V20h-4V8.5H3z"/>
          </svg>
        )}
        {company.id === "csgp" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#003DA5" }}>
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z"/>
          </svg>
        )}
      </div>

      {/* Company Info */}
      <div className="text-center">
        <h3
          className="text-base font-semibold"
          style={{ color: "var(--text-primary)" }}
        >
          {company.name}
        </h3>
        <p
          className="mt-1 text-xs uppercase tracking-wider"
          style={{ color: "var(--text-secondary)" }}
        >
          Sector: {company.sector}
        </p>
        <p
          className="mt-0.5 text-xs"
          style={{ color: "var(--text-tertiary)" }}
        >
          Marktcap.: {company.marketCap}
        </p>
        {/* Historical Data Indicator */}
        {company.historicalNewsAvailable && (
          <div
            className="mt-2 inline-flex items-center gap-1 rounded-full px-2 py-1 text-[10px] font-medium"
            style={{
              backgroundColor: "color-mix(in srgb, var(--accent) 10%, transparent)",
              color: "var(--accent)",
            }}
          >
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Historical Data (2000-2023)
          </div>
        )}
      </div>
    </button>
  );
}

