export default function ResultList({
  title,
  subtitle,
  items = [],
  variant = "default",
}) {
  return (
    <section className={`panel result-panel ${variant}`}>
      <div className="panel-heading">
        <h3>{title}</h3>
        {subtitle && <p>{subtitle}</p>}
      </div>

      <div className="result-list">
        {items.map((item, index) => (
          <div className="result-row" key={`${title}-${index}`}>
            <span className="result-marker" aria-hidden="true">
              {variant === "strength" ? "✓" : variant === "weakness" ? "↗" : "•"}
            </span>
            <span>{item}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
