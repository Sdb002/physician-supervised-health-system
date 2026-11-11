import type { ExerciseItem } from "@/lib/api";
import { conditionName, equipmentName, localName, needsEquipment } from "@/lib/clinical-terms";
import type { Lang } from "@/lib/use-lang";
import { IconYoutube } from "@/components/icons";
import { buttonSecondary } from "@/components/ui";

const LABELS = {
  en: {
    needs: (e: string) => `Needs: ${e}`,
    easierFirst: "Start with the easier version:",
    howTo: "How to do it",
    easier: "Easier version:",
    takeCare: "Take care:",
    video: "Watch on YouTube",
    similarVideo: "Watch a similar exercise on YouTube",
    newTab: "(opens in a new tab)",
    source: "Source",
  },
  bn: {
    needs: (e: string) => `লাগবে: ${e}`,
    easierFirst: "সহজ রূপটি দিয়ে শুরু করুন:",
    howTo: "কীভাবে করবেন",
    easier: "সহজ রূপ:",
    takeCare: "সাবধান:",
    video: "ইউটিউবে দেখুন",
    similarVideo: "একই ধরনের ব্যায়াম ইউটিউবে দেখুন",
    newTab: "(নতুন ট্যাবে খুলবে)",
    source: "উৎস",
  },
} as const;

/**
 * One exercise of the prescription: its name and dose, what this patient
 * should do differently (the easier version at 65 and over, the dataset's
 * note for each of their conditions it is allowed with care for), a button to
 * its demonstration video on YouTube (labelled as a similar exercise when the
 * dataset found no exact match), and, on request, how to do it. `compact`
 * keeps the name, dose and cautions only (the printed report). The dataset's
 * text is English; a plan made before engine 0.12.0 has only a name.
 */
export function ExerciseItemView({
  ex,
  lang,
  compact = false,
  staff = false,
}: {
  ex: ExerciseItem;
  lang: Lang;
  compact?: boolean;
  staff?: boolean;
}) {
  const t = LABELS[lang];
  const cautions = (ex.condition_notes ?? []).filter((n) => n.modify);
  const showEasierFirst = Boolean(ex.use_easier_version && ex.easier_version);
  const hasDetails = Boolean(
    ex.how_to || ex.safety_notes || (ex.easier_version && !showEasierFirst) || (staff && ex.source?.name),
  );
  // staff read the source's own dose; patients the engine's plain version
  const dose = staff ? ex.dose_source || ex.dose : ex.dose;

  return (
    <div>
      <p className="font-medium text-ink">{localName(ex, lang)}</p>
      {dose && <p className="text-sm text-ink-soft">{dose}</p>}
      {!compact && needsEquipment(ex.equipment) && (
        <p className="text-sm text-ink-muted">{t.needs(equipmentName(ex.equipment, lang))}</p>
      )}
      {showEasierFirst && (
        <p className="mt-1.5 text-sm text-ink-strong">
          <span className="font-semibold">{t.easierFirst}</span> {ex.easier_version}
        </p>
      )}
      {cautions.map((n) => (
        <p key={n.condition} className="mt-1.5 border-l-2 border-watch-mark pl-2 text-sm text-ink-strong">
          <span className="font-semibold">{conditionName(n.condition, lang)}:</span> {n.note}
        </p>
      ))}
      {!compact && ex.video && (
        <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1">
          <a href={ex.video.url} target="_blank" rel="noopener noreferrer" className={buttonSecondary}>
            <IconYoutube className="h-5 w-5 shrink-0" />
            {ex.video.match === "exact" ? t.video : t.similarVideo}
            <span className="sr-only"> {t.newTab}</span>
          </a>
          {ex.video.channel && <span className="text-sm text-ink-muted">{ex.video.channel}</span>}
        </div>
      )}
      {!compact && hasDetails && (
        <details className="mt-2">
          <summary className="cursor-pointer text-sm font-semibold text-clinical hover:underline">
            {t.howTo}
          </summary>
          <div className="mt-1.5 space-y-1.5 text-sm leading-6 text-ink-soft">
            {ex.how_to && <p>{ex.how_to}</p>}
            {ex.easier_version && !showEasierFirst && (
              <p>
                <span className="font-semibold text-ink-strong">{t.easier}</span> {ex.easier_version}
              </p>
            )}
            {ex.safety_notes && (
              <p>
                <span className="font-semibold text-ink-strong">{t.takeCare}</span> {ex.safety_notes}
              </p>
            )}
            {staff && ex.source?.name && (
              <p className="text-ink-muted">
                {t.source}:{" "}
                {ex.source.url ? (
                  <a href={ex.source.url} target="_blank" rel="noopener noreferrer" className="hover:underline">
                    {ex.source.name}
                  </a>
                ) : (
                  ex.source.name
                )}
              </p>
            )}
          </div>
        </details>
      )}
    </div>
  );
}
