// Walk the Archive - runtime module rules.
// Dependencies are the contract list (CONTRACT.md section 4). Nothing else in phase 0.

using UnrealBuildTool;

public class WalkTheArchive : ModuleRules
{
	public WalkTheArchive(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"EnhancedInput",
			"UMG",
			"Slate",
			"SlateCore",
			"AIModule",
			"NavigationSystem",
			"DeveloperSettings",
			"Json",
			"JsonUtilities"
		});

		// AudioCaptureCore: the Lost Stories booth's microphone (Audio::FAudioCapture; the AudioCapture plugin, on by
		// default, loads the platform's capture back end).
		PrivateDependencyModuleNames.AddRange(new string[] { "AnimationCore", "AudioCaptureCore" });
	}
}
