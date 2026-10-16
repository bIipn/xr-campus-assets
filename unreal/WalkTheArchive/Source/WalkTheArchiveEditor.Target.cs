// Walk the Archive - editor target.

using UnrealBuildTool;
using System.Collections.Generic;

public class WalkTheArchiveEditorTarget : TargetRules
{
	public WalkTheArchiveEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("WalkTheArchive");
	}
}
