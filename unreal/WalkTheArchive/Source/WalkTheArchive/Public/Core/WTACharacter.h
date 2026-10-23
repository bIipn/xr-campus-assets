// Walk the Archive - the first-person player.
//
// Feel constants are ports of the web build (nav.js / world.js): eye at 162 cm, capsule 90 x 30, walk 300 cm/s,
// sprint 560, jump 520, gravity scale 1.63, head-bob 2.6 cm with a 155 cm stride, landing dip spring.
// WalkTo uses the NavMesh through UAIBlueprintHelperLibrary::SimpleMoveToLocation (adds a path-following
// component to the player controller) and raises MaxWalkSpeed to clamp(PathLength / 2.3, 240, 1200) while it walks.
//
// Guided visits (UWTAVisitSubsystem): the pawn replicates, always relevant, and its owner's machine has the say over
// where it is (client-authoritative movement: teleports, sitting and the tour's walks need no server correction).
// Other people see it as a figure in the person's colour (AWTAPlayerState) with their name over it
// (UWTANameTagWidget): the designed one from bl/figure.py (/Game/WTA/Campus/People: a robe, arms, a head that tilts
// with the person's look and a headset visor showing which way they face, a collar ring), or, before that is
// imported, the engine's basic shapes. Nobody sees their own figure, and one within arm's reach of the camera hides.
// Sitting reaches the others through ServerSetSeated (the seated figure sits on the seat, hands on the lap).
// Players never block each other.
//
// VR (docs/VR_MODE.md): StartVR puts a UWTAVRRig on the player (the head on a floor-level origin, the hands, the
// laser); with a headset, TeleportToView puts the head (not the capsule) over the view's floor point facing its yaw,
// sitting lowers the origin to a seated eye height, and the camera has no bob or dip. In VR the other people's name
// tags draw in the world, facing the eye (a screen-space widget does not reach the headset).

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "Engine/EngineTypes.h"
#include "Data/WTATypes.h"
#include "WTACharacter.generated.h"

class UCameraComponent;
class UMaterialInstanceDynamic;
class UMaterialInterface;
class UStaticMesh;
class UStaticMeshComponent;
class UWidgetComponent;
class UWTAVRRig;

/** The player sat down on Seat (bSeated) or stood up from it. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FWTASeatChanged, AActor*, Seat, bool, bSeated);

UCLASS(Blueprintable)
class WALKTHEARCHIVE_API AWTACharacter : public ACharacter
{
	GENERATED_BODY()

public:
	AWTACharacter();

	/** First-person camera, relative Z = EyeHeight - capsule half height (72 cm) plus bob/dip. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WTA")
	TObjectPtr<UCameraComponent> Camera;

	// --- Feel (cm, cm/s, seconds) --------------------------------------------

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float WalkSpeed = 300.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float SprintSpeed = 560.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float EyeHeight = 162.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float BobAmplitude = 2.6f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float BobStride = 155.f;

	/** Landing dip: impulse = -fall speed * this (web 0.1), spring (110, 15). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float LandingDipScale = 0.1f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float TravelSpeedMin = 240.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float TravelSpeedMax = 1200.f;

	/** Auto-walk stops within this distance of the goal. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float AutoWalkStopRadius = 10.f;

	// --- Movement API ----------------------------------------------------------

	/** Walk to a floor point on the NavMesh (click-to-walk, tour stops, places). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void WalkTo(FVector Dest);

	/** Cancel the current auto-walk (any manual move input also cancels it). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void StopWalking();

	/** True while a WalkTo path is being followed. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsAutoWalking() const;

	/** Put the player at View.Location (eye) facing View.Yaw/Pitch, no walk. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void TeleportToView(const FWTAView& View);

	/** The current eye position and control rotation as a view (bValid true). */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FWTAView GetCurrentView() const;

	/** Camera world position. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FVector GetEyeLocation() const;

	/** Shift / left thumb: switches MaxWalkSpeed between WalkSpeed and SprintSpeed. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void SetSprinting(bool bOn);

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsSprinting() const { return bSprinting; }

	/** Move input from the controller: X = right, Y = forward, relative to the control yaw. Cancels auto-walk. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void AddMoveInput(FVector2D Axis);

	// --- Sitting -----------------------------------------------------------------

	/**
	 * Sits down on Seat: the capsule shortens and stands on the floor under the sit point, the eye settles
	 * SeatEyeHeight above SeatTop facing Yaw, and movement is locked. Looking and every interaction keep working.
	 * Where the player stood is kept, so standing up puts them back on the floor there.
	 */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void SitAt(AActor* Seat, const FVector& SeatTop, float Yaw);

	/** Stands up: the capsule and movement come back; bReturn puts the player back where they sat down from. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void StandUp(bool bReturn = true);

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsSeated() const { return bSeated; }

	/** The seat sat on (null when standing). */
	UFUNCTION(BlueprintPure, Category = "WTA")
	AActor* GetSeat() const { return Seat.Get(); }

	/** The eye above the seat's top when sitting: 120 cm off the floor on a 45 cm chair. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float SeatEyeHeight = 75.f;

	/** Fired after SitAt and StandUp (a talk starts when its venue's seat is taken). */
	UPROPERTY(BlueprintAssignable, Category = "WTA")
	FWTASeatChanged OnSeatChanged;

	// --- In a guided visit: the figure the others see --------------------------------

	/** The figure's root, on the floor under the capsule. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WTA|Visit")
	TObjectPtr<USceneComponent> Figure;

	UPROPERTY(VisibleAnywhere, Category = "WTA|Visit")
	TObjectPtr<UStaticMeshComponent> FigureBase;

	UPROPERTY(VisibleAnywhere, Category = "WTA|Visit")
	TObjectPtr<UStaticMeshComponent> FigureBody;

	UPROPERTY(VisibleAnywhere, Category = "WTA|Visit")
	TObjectPtr<UStaticMeshComponent> FigureShoulders;

	/** The neck: the head and visor turn about it with the person's look. */
	UPROPERTY(VisibleAnywhere, Category = "WTA|Visit")
	TObjectPtr<USceneComponent> FigureNeck;

	UPROPERTY(VisibleAnywhere, Category = "WTA|Visit")
	TObjectPtr<UStaticMeshComponent> FigureHead;

	UPROPERTY(VisibleAnywhere, Category = "WTA|Visit")
	TObjectPtr<UStaticMeshComponent> FigureVisor;

	/** The name over the figure (screen space, so it reads at any distance; hidden behind walls). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WTA|Visit")
	TObjectPtr<UWidgetComponent> NameTag;

	/** Seated, as the others see it (its owner sets it through ServerSetSeated). */
	UPROPERTY(ReplicatedUsing = OnRep_SeatedPose, BlueprintReadOnly, Category = "WTA|Visit")
	bool bSeatedPose = false;

	/** True when the figure shows on this machine (another person's pawn in a visit). */
	UFUNCTION(BlueprintPure, Category = "WTA|Visit")
	bool IsFigureShown() const { return bFigureShown; }

	/** A look-dev stand-in (AWTAPlayerController::WTAFigures): its figure shows in a solo game too. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA|Visit")
	bool bStandIn = false;

	/** True when the figure is the designed one (bl/figure.py) rather than the basic shapes. */
	UFUNCTION(BlueprintPure, Category = "WTA|Visit")
	bool IsDesignedFigure() const { return bDesignedFigure; }

	/** True once the name tag shows (in range and not behind a wall). */
	UFUNCTION(BlueprintPure, Category = "WTA|Visit")
	bool IsNameTagShown() const { return bFigureShown && !bTagHidden; }

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	// --- VR ----------------------------------------------------------------------------

	/** Go into VR on this player (AWTAPlayerController::EnterVR): the rig with its hands and laser; bHeadset = a real
	    headset, else the desktop simulation. */
	void StartVR(bool bHeadset);

	/** Back to the desktop camera. */
	void StopVR();

	/** The VR rig, or null on the desktop. */
	UWTAVRRig* GetVRRig() const { return VRRig; }

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void Landed(const FHitResult& Hit) override;
	virtual void OnRep_PlayerState() override;

	/** The owner sat down (Location = the seated capsule centre) or stood up (Location = where they stand). */
	UFUNCTION(Server, Reliable)
	void ServerSetSeated(bool bOn, FVector_NetQuantize Location, float Yaw);

	UFUNCTION()
	void OnRep_SeatedPose();

	/** Tell the others about sitting down or standing up (the guide's own pawn sets the pose directly). */
	void ShareSeated(bool bOn);

	/** Every tick: show the figure only for another person's pawn in a visit, hide it at arm's reach of the camera
	    and the name tag behind walls or far off, tilt the head with the look, follow the seated pose. */
	void UpdateFigure(float DeltaSeconds);

	/** Colours and the name tag from the player state (when they change). */
	void RefreshFigureLook();

	/** Lay the parts out standing or seated (lower and shorter, sitting on the seat). */
	void LayoutFigure(bool bSitting);

	/** The designed figure's meshes (and M_WTA_Figure), the first time a figure shows; the basic shapes stay when they
	    are not imported. */
	void LoadFigureMeshes();

	UPROPERTY(Transient)
	TObjectPtr<UStaticMesh> StandingMesh;

	UPROPERTY(Transient)
	TObjectPtr<UStaticMesh> SeatedMesh;

	/** What the figure's colours are made on: M_WTA_Figure (Color, Roughness, Sheen), else BasicShapeMaterial (Color). */
	UPROPERTY(Transient)
	TObjectPtr<UMaterialInterface> FigureLook;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> CollarMaterial;

	/** The engine's BasicShapeMaterial, the colours' base when M_WTA_Figure is not built. */
	UPROPERTY()
	TObjectPtr<UMaterialInterface> ShapeLook;

	bool bFigureMeshesTried = false;
	bool bDesignedFigure = false;
	bool bTagLogged = false;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> FigureMaterial;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> HeadMaterial;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> VisorMaterial;

	UPROPERTY(Transient)
	TObjectPtr<UWTAVRRig> VRRig;

	/** In VR the name tag draws in the world, facing the eye (made on first use); NameTag is screen space. */
	UPROPERTY(Transient)
	TObjectPtr<UWidgetComponent> NameTagWorld;

	/** The world-space name tag, made the first time VR needs it. */
	UWidgetComponent* WorldNameTag();

	/** The name tag in use: in the world in VR, else on the screen. */
	UWidgetComponent* ActiveNameTag();

	/** Both name tags at Relative over the figure's root. */
	void PlaceNameTags(const FVector& Relative);

	/** The tag in use is the world one (VR). */
	bool bTagInWorld = false;

	bool bFigureShown = false;
	bool bFigureLaidSeated = false;
	bool bTagHidden = true;
	FString ShownName;
	int32 ShownSlot = -1;
	bool bShownGuide = false;
	float SinceLook = 0.f;
	float SinceTagCheck = 0.f;

	/** Head-bob + landing-dip camera offset (port of playerFrame, nav.js). */
	void UpdateCameraOffset(float DeltaSeconds);

	/** Adds the XY distance moved this frame to UWTAProgressSubsystem::NoteDistance. */
	void NoteDistanceWalked();

	bool bSeated = false;
	TWeakObjectPtr<AActor> Seat;
	/** The capsule's location before sitting down, to stand back up at. */
	FVector StandLocation = FVector::ZeroVector;
	/** The camera's height over the capsule centre while seated. */
	float SeatedCameraZ = 0.f;
	/** The eye's world height while seated (VR puts a headset's eyes there). */
	float SeatedEyeZ = 0.f;

	float BobPhase = 0.f;
	/** 0..1 bob strength, eased toward the measured ground speed (web PLAYER.amp). */
	float BobAmount = 0.f;
	float DipOffset = 0.f;
	float DipVelocity = 0.f;
	bool bSprinting = false;
	bool bAutoWalking = false;
	FVector LastFrameLocation = FVector::ZeroVector;
	bool bHasLastFrameLocation = false;
};
