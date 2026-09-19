import type { Tutorial } from '../../types/tutorial';
import './TutorialCard.css';

interface TutorialCardProps {
  tutorial: Tutorial;
  onVideoClick: (tutorial: Tutorial) => void;
}

export default function TutorialCard({
  tutorial,
  onVideoClick,
}: TutorialCardProps) {
  return (
    <article className="tutorial-card">
      <button
        type="button"
        className="tutorial-card-video"
        onClick={() => onVideoClick(tutorial)}
        aria-label={`پخش آموزش ${tutorial.title}`}
      >
        <img
          src={tutorial.thumbnail}
          alt={`پوستر ${tutorial.title}`}
          className="tutorial-card-thumbnail"
        />

        <span className="tutorial-card-play" aria-hidden="true">
          <i className="bi bi-play-fill" />
        </span>
      </button>

      <div className="tutorial-card-body">
        <h2 className="tutorial-card-title">{tutorial.title}</h2>

        <p className="tutorial-card-description">
          {tutorial.description}
        </p>

        <span className="tutorial-card-type">{tutorial.type}</span>
      </div>
    </article>
  );
}
