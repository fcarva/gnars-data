import type { ActivityViewScene } from "../types";

export function ActivityChart({
  scene,
  title,
  detail,
}: {
  scene: ActivityViewScene;
  title?: string;
  detail?: string;
}) {
  const latest = scene.points[scene.points.length - 1];

  return (
    <article className="chart-card">
      {(title || detail) && (
        <div className="chart-head">
          {title ? <strong>{title}</strong> : null}
          {detail ? <span>{detail}</span> : null}
        </div>
      )}
      <svg
        aria-label={title ?? scene.label}
        className="activity-chart"
        viewBox={`0 0 ${scene.width} ${scene.height}`}
        role="img"
      >
        <path className="activity-path governance" d={scene.paths.governance ?? ""} />
        <path className="activity-path treasury" d={scene.paths.treasury ?? ""} />
        <path className="activity-path deliveries" d={scene.paths.deliveries ?? ""} />
      </svg>
      <div className="chart-legend">
        <span className="governance">Governance</span>
        <span className="treasury">Treasury</span>
        <span className="deliveries">Deliveries</span>
      </div>
      {latest ? (
        <div className="chart-foot">
          <small>Latest point: {latest.date}</small>
          <small>{scene.label}</small>
        </div>
      ) : null}
    </article>
  );
}
